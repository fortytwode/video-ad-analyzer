"""
Video content extraction module.

Handles all video processing including:
- Frame extraction with scene change detection
- OCR text detection
- Audio extraction and transcription
- Visual content analysis
"""

import os
import cv2
import base64
from PIL import Image
import io
import easyocr
import numpy as np
from collections import defaultdict
import subprocess
import traceback
from skimage.metrics import structural_similarity
import logging
import time
import re
import difflib
from google.api_core import exceptions as google_exceptions
from vertexai.generative_models import GenerativeModel, GenerationConfig, Part
from google.cloud import speech

logger = logging.getLogger(__name__)


def retry_with_backoff(func, max_retries=5, initial_delay=10):
    """
    Retry a function with exponential backoff for transient errors.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts (default: 5)
        initial_delay: Initial delay in seconds (default: 10)
    
    Returns:
        Function result if successful
        
    Raises:
        Last exception if all retries fail
    """
    for attempt in range(max_retries):
        try:
            return func()
        except (google_exceptions.ServiceUnavailable, 
                google_exceptions.InternalServerError,
                google_exceptions.ResourceExhausted,  # 429 rate limit
                ConnectionError) as e:
            if attempt == max_retries - 1:
                logger.error(f"All {max_retries} retry attempts failed")
                raise
            
            delay = initial_delay * (2 ** attempt)  # Exponential backoff
            logger.warning(f"API error (attempt {attempt + 1}/{max_retries}): {str(e)}")
            logger.info(f"Retrying in {delay} seconds...")
            time.sleep(delay)
        except Exception as e:
            # For non-transient errors, fail immediately
            logger.error(f"Non-retryable error: {str(e)}")
            raise


class VideoExtractor:
    """Handles video content extraction including frames, text, and audio."""
    
    def __init__(self, gemini_model=None, temp_dir=None, prompt_manager=None):
        """
        Initialize VideoExtractor.

        Args:
            gemini_model: Gemini model instance for vision/transcription analysis
            temp_dir: Directory for temporary files (audio, frames, etc.)
            prompt_manager: PromptManager instance for external prompts (optional)
        """
        self.gemini_model = gemini_model
        self.prompt_manager = prompt_manager
        self.temp_dir = temp_dir or "/tmp/video_analysis"
        
        # Create temp directory if it doesn't exist
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Initialize EasyOCR reader
        self.reader = easyocr.Reader(['en'])
        self.text_memory = defaultdict(int)
        self.transcription_history = []
        
        # Cost tracking
        self.cost_tracking = {
            'gemini-2.0-flash': {'calls': 0, 'images': 0, 'cost': 0, 'tokens': {'input': 0, 'output': 0}},
        }
    
    def _calculate_cost(self, model, input_tokens=0, output_tokens=0, num_images=0):
        """Calculate cost based on model usage."""
        costs = {
            'gemini-2.0-flash': {'input': 0.0001, 'output': 0.0004, 'image': 0.00765}
        }
        
        if model not in costs:
            return 0
        
        # Update token counts
        self.cost_tracking[model]['tokens']['input'] += input_tokens
        self.cost_tracking[model]['tokens']['output'] += output_tokens
        self.cost_tracking[model]['calls'] += 1
        
        # Calculate cost
        token_cost = (
            (input_tokens / 1000) * costs[model]['input'] +
            (output_tokens / 1000) * costs[model]['output']
        )
        
        # Add image cost
        image_cost = 0
        if num_images > 0:
            image_cost = num_images * costs[model]['image']
            self.cost_tracking[model]['images'] += num_images
        
        total_cost = token_cost + image_cost
        self.cost_tracking[model]['cost'] += total_cost
        
        logger.debug(f"Cost: {model} - ${total_cost:.6f} (tokens: {input_tokens}/{output_tokens}, images: {num_images})")
        
        return total_cost
    
    def detect_scene_change(self, frame1, frame2, threshold=65):
        """Detect if two frames are significantly different."""
        if frame1 is None or frame2 is None:
            return True
        
        # Convert frames to grayscale
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        # Calculate structural similarity index
        score, _ = structural_similarity(gray1, gray2, full=True)
        similarity_threshold = threshold / 100
        logger.debug(f"Scene SSIM score: {score:.4f} | Threshold: {similarity_threshold:.2f}")
        
        return score < similarity_threshold
    
    def is_similar_text(self, text1, text2, threshold=0.8):
        """Check if two texts are similar using string similarity."""
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        if text1 == text2:
            return True
        
        if text1 in text2 or text2 in text1:
            return True
        
        # Calculate similarity score
        words1 = set(text1.split())
        words2 = set(text2.split())
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union > threshold if union > 0 else 0
    
    def filter_detected_text(self, text_list, frame_timestamp):
        """Basic pre-filtering of detected text."""
        if not text_list:
            return []
        
        cleaned_texts = []
        for text in text_list:
            clean_text = text.strip('[]"\' ').upper()
            
            if len(clean_text) < 3:
                continue
            
            if any(self.is_similar_text(clean_text, existing) for existing in cleaned_texts):
                continue
            
            cleaned_texts.append(clean_text)
        
        return cleaned_texts
    
    def proofread_detected_text(self, text_list, timestamp):
        """Clean OCR results without modifying content."""
        if not text_list:
            return []
        
        batch_size = 20
        delay = 1.5
        cleaned_text = []
        total_batches = (len(text_list) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start = batch_num * batch_size
            end = start + batch_size
            batch = text_list[start:end]
            
            try:
                prompt_text = f"""Given these OCR-detected text strings:
{batch}

ONLY fix these specific OCR errors:
1. Fix obvious spelling mistakes (e.g. 'nutriti0nal' -> 'nutritional')
2. Fix spacing issues (e.g. 'working1on1' -> 'working 1-on-1')
3. Fix character confusion (e.g. '0' vs 'O', 'l' vs 'I')

Rules:
- DO NOT change the meaning or structure
- DO NOT combine or split texts
- DO NOT remove any text
- Return exact same number of items
- If text looks correct, return as is

Return each text on a new line, in same order."""
                
                response = retry_with_backoff(
                    lambda: self.gemini_model.generate_content(prompt_text),
                    max_retries=5,
                    initial_delay=10
                )
                
                self._calculate_cost(
                    model='gemini-2.0-flash',
                    input_tokens=response.usage_metadata.prompt_token_count,
                    output_tokens=response.usage_metadata.total_token_count
                )
                
                cleaned_batch = response.text.strip().split('\n')
                
                if len(cleaned_batch) != len(batch):
                    logger.warning(f"Gemini changed number of items in batch {batch_num + 1} at {timestamp}s")
                    cleaned_text.extend(batch)
                else:
                    cleaned_text.extend([line.strip() for line in cleaned_batch])
                
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error cleaning batch {batch_num + 1} at {timestamp}s: {str(e)}")
                cleaned_text.extend(batch)
        
        return cleaned_text
    
    def detect_text_in_frame(self, frame, timestamp):
        """Detect text in a frame using tiered confidence thresholds."""
        try:
            results = self.reader.readtext(frame)
            high_confidence_text = []
            low_confidence_text = []
            
            for (bbox, text, prob) in results:
                clean_text = text.strip()
                if not clean_text:
                    continue
                
                if prob > 0.5:
                    high_confidence_text.append(clean_text)
                elif prob > 0.3:
                    low_confidence_text.append(clean_text)
            
            # Use lower confidence results only when high confidence is sparse
            if len(high_confidence_text) < 3:
                detected_text = high_confidence_text + low_confidence_text
            else:
                detected_text = high_confidence_text
            
            return detected_text if detected_text else []
            
        except Exception as e:
            logger.error(f"Error in OCR: {str(e)}")
            return []
    
    def is_similar_text_timeline(self, text1, text2, threshold=0.65):
        """Determine if two texts are similar using SequenceMatcher."""
        text1_lower = ' '.join(text1).lower()
        text2_lower = ' '.join(text2).lower()
        return difflib.SequenceMatcher(None, text1_lower, text2_lower).ratio() >= threshold
    
    def deduplicate_from_single_sentence(self, new_tokens, timestamp, similarity_threshold=0.65):
        """Compare current sentence to most recent saved one."""
        new_text = new_tokens
        
        if self.transcription_history:
            last_text, last_time = self.transcription_history[-1]
            
            if self.is_similar_text_timeline(new_text, last_text, threshold=similarity_threshold):
                self.transcription_history[-1] = (new_text, timestamp)
                return new_text
            else:
                self.transcription_history.append((new_text, timestamp))
                return new_text
        else:
            self.transcription_history.append((new_text, timestamp))
            return new_text
    
    def process_new_text(self, detected_text, current_time, text_timeline, similarity_threshold=0.65):
        """Process new detected text, deduplicate, and maintain unique timeline entries."""
        deduplicated = self.deduplicate_from_single_sentence(detected_text, current_time, similarity_threshold)
        if not deduplicated:
            return []
        
        found_in_timeline = False
        for i, item in enumerate(text_timeline):
            if self.is_similar_text_timeline(deduplicated, item['text'], threshold=similarity_threshold):
                logger.debug("Found similar transcription in timeline. Replacing with new deduplicated one.")
                text_timeline[i] = {'at': current_time, 'text': deduplicated}
                found_in_timeline = True
                break
        
        if not found_in_timeline:
            text_timeline.append({'at': current_time, 'text': deduplicated})
        
        self.transcription_history[-1] = (deduplicated, current_time)
        return text_timeline

    def extract_content(self, file_path):
        """
        Main extraction router - handles both videos and images.

        Returns same structure as extract_smart_frames:
            vision_frames, vision_timestamps, text_timeline
        """
        logger.info(f"Starting content extraction for: {file_path}")

        # Route based on file extension
        if self._is_image_file(file_path):
            return self._extract_image_content(file_path)
        else:
            return self.extract_smart_frames(file_path)

    def _is_image_file(self, file_path):
        """Check if file is an image."""
        image_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff')
        return file_path.lower().endswith(image_extensions)

    def _extract_image_content(self, image_path):
        """
        Extract content from image - creates video-compatible data.

        Returns same structure as extract_smart_frames:
            vision_frames, vision_timestamps, text_timeline
        """
        logger.info(f"Processing image: {image_path}")

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        try:
            # Load image and convert to base64
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')

            # OCR text extraction using existing logic
            text_timeline = []
            if self.reader:
                try:
                    image = Image.open(image_path)
                    results = self.reader.readtext(np.array(image))
                    for (bbox, text, confidence) in results:
                        if confidence > 0.5 and text.strip():
                            # Check if text already exists in timeline
                            text_exists = any(
                                text.strip() in entry.get('text', [])
                                for entry in text_timeline
                            )
                            if not text_exists:
                                text_timeline.append({
                                    'at': 0.0,
                                    'text': [text.strip()]
                                })
                    logger.info(f"Extracted {len(text_timeline)} text elements from image")
                except Exception as e:
                    logger.warning(f"OCR extraction failed: {e}")

            # Return same format as extract_smart_frames
            # Images are treated as single-frame videos at t=0
            vision_frames = [image_b64]
            vision_timestamps = [0.0]

            logger.info(f"Image extraction complete: 1 frame, {len(text_timeline)} text elements")
            return vision_frames, vision_timestamps, text_timeline

        except Exception as e:
            logger.error(f"Error extracting image content: {str(e)}")
            raise

    def extract_smart_frames(self, video_path, scene_interval=2, text_interval=0.5):
        """Extract frames with temporal deduplication."""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        video = cv2.VideoCapture(video_path)
        if not video.isOpened():
            raise ValueError("Failed to open video file")
        
        fps = video.get(cv2.CAP_PROP_FPS)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        vision_frames = []
        vision_timestamps = []
        text_timeline = []
        all_detected_text = []
        
        prev_frame = None
        last_scene_time = -scene_interval
        frame_count = 0
        
        logger.info(f"Checking frames every {text_interval}s for text and {scene_interval}s for scenes...")
        
        current_time = 0
        while current_time < duration:
            frame_idx = int(current_time * fps)
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = video.read()
            
            if not ret:
                break
            
            # Check for scene changes
            if current_time - last_scene_time >= scene_interval:
                if self.detect_scene_change(prev_frame, frame, threshold=65):
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    pil_image = Image.fromarray(frame_rgb)
                    
                    img_byte_arr = io.BytesIO()
                    pil_image.save(img_byte_arr, format='JPEG')
                    base64_frame = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                    
                    vision_frames.append(base64_frame)
                    vision_timestamps.append(current_time)
                    frame_count += 1
                    logger.info(f"Saved scene frame at {current_time:.2f}s (Frame {frame_count})")
                    
                    # Detect text
                    detected_text = self.detect_text_in_frame(frame, current_time)
                    if detected_text:
                        all_detected_text.append((detected_text, current_time))
                        logger.debug(f"Collected text at {current_time:.2f}s")
                    
                    prev_frame = frame
                else:
                    logger.debug(f"Skipped similar frame at {current_time:.2f}s")
                
                last_scene_time = current_time
            
            current_time += text_interval
        
        video.release()
        logger.info(f"Extracted {frame_count} distinct scene frames")
        
        # Process all collected text
        if all_detected_text:
            logger.info(f"Processing {len(all_detected_text)} text entries")
            for text, time in all_detected_text:
                text_timeline = self.process_new_text(text, time, text_timeline)
        
        return vision_frames, vision_timestamps, text_timeline
    
    def process_text_timeline(self, text_timeline, window_size=2.0):
        """Group text fragments that appear within a time window."""
        if not text_timeline or len(text_timeline) <= 1:
            return text_timeline
        
        sorted_entries = sorted(text_timeline, key=lambda x: x['at'])
        
        i = 0
        processed_timeline = []
        while i < len(sorted_entries):
            current_entry = sorted_entries[i]
            window_end = current_entry['at'] + window_size
            
            window_entries = [current_entry]
            j = i + 1
            while j < len(sorted_entries) and sorted_entries[j]['at'] <= window_end:
                window_entries.append(sorted_entries[j])
                j += 1
            
            # Combine all text in this window
            all_text = []
            for entry in window_entries:
                all_text.extend(entry['text'])
            
            # Remove duplicates while preserving order
            seen = set()
            unique_text = [x for x in all_text if not (x in seen or seen.add(x))]
            
            processed_entry = {
                'at': current_entry['at'],
                'duration': window_entries[-1]['at'] - current_entry['at'] + 0.5,
                'text': unique_text
            }
            
            processed_timeline.append(processed_entry)
            i = j
        
        return processed_timeline
    
    def analyze_frames_batch(self, frames, timestamps, texts, batch_size=None):
        """Analyze multiple frames using Gemini."""
        frame_descriptions = []
        descriptions_by_time = {}
        
        batch_frames = frames
        batch_times = [float(t) for t in timestamps]
        batch_texts = texts
        logger.info(f"Analyzing all {len(frames)} frames in a single batch")
        
        try:
            if self.gemini_model:
                # Use Gemini for analysis
                prompt_text = """Analyze these sequential frames from a marketing video. For each frame:
1. What's happening in this specific moment?
2. Note any text overlays (including: """ + str([t for sublist in batch_texts for t in sublist]) + """)
3. Focus on changes from previous frame
4. Maximum 2 sentences per frame
5. Ignore static elements unless newly relevant

REQUIRED FORMAT: For each frame, your response MUST follow this EXACT format:
Frame [timestamp]: [1-2 concise sentences about what's new]

For example:
Frame 2.50: A person demonstrates the product with an excited expression. Text overlay shows "AMAZING RESULTS".

DO NOT deviate from this format. Each frame description MUST start with "Frame" followed by the timestamp."""
                
                content_parts = [Part.from_text(prompt_text)]
                
                # Add each frame and timestamp
                for frame_b64, timestamp in zip(batch_frames, batch_times):
                    image_bytes = base64.b64decode(frame_b64)
                    content_parts.append(Part.from_text(f"Frame at {timestamp:.2f}s:"))
                    content_parts.append(Part.from_data(image_bytes, mime_type="image/jpeg"))
                
                # Generate content using Gemini with retry
                response = retry_with_backoff(
                    lambda: self.gemini_model.generate_content(
                        contents=content_parts,
                        generation_config=GenerationConfig(
                            temperature=0.2,
                            max_output_tokens=2000,
                            top_p=0.95,
                        )
                    ),
                    max_retries=5,
                    initial_delay=10
                )
                
                logger.debug(f"Gemini response: {response}")
                
                # Track costs
                self._calculate_cost(
                    model='gemini-2.0-flash',
                    input_tokens=response.usage_metadata.prompt_token_count,
                    output_tokens=response.usage_metadata.total_token_count,
                    num_images=len(batch_frames)
                )
                
                # Parse response with regex
                description_text = response.text
                frame_pattern = re.compile(r'Frame\s+(\d+\.\d+)(?:s)?:\s*(.*?)(?=Frame\s+\d+\.\d+|$)', re.DOTALL)
                matches = frame_pattern.findall(description_text)
                
                if matches:
                    for timestamp_str, description in matches:
                        try:
                            timestamp = float(timestamp_str)
                            description = description.strip()
                            
                            frame_descriptions.append({
                                "timestamp": timestamp,
                                "description": description
                            })
                            descriptions_by_time[timestamp] = description
                        except Exception as e:
                            logger.error(f"Error parsing frame description: {str(e)}")
                            continue
                else:
                    # Fallback to line-by-line parsing
                    for line in description_text.split('\n'):
                        if line.strip().startswith('Frame'):
                            try:
                                parts = line.split(':', 1)
                                if len(parts) == 2:
                                    timestamp = float(parts[0].strip().split()[1].rstrip('s'))
                                    description = parts[1].strip()
                                    
                                    frame_descriptions.append({
                                        "timestamp": timestamp,
                                        "description": description
                                    })
                                    descriptions_by_time[timestamp] = description
                            except Exception as e:
                                logger.error(f"Error parsing frame description: {str(e)}")
                                continue
        except Exception as e:
            logger.error(f"Error in batch analysis: {str(e)}")
            traceback.print_exc()
        
        return frame_descriptions, descriptions_by_time
    
    def extract_audio(self, video_path, output_path):
        """Extract audio from video file."""
        try:
            logger.info(f"Starting audio extraction from {video_path}")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Extract audio to WAV
            command = [
                'ffmpeg',
                '-i', video_path,
                '-vn',
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                '-y',
                output_path
            ]
            
            logger.info(f"Running ffmpeg command: {' '.join(command)}")
            process = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"Audio extraction completed with return code: {process.returncode}")
            
            # Convert to MP3
            mp3_path = output_path + ".mp3"
            mp3_command = [
                'ffmpeg',
                '-i', output_path,
                '-codec:a', 'libmp3lame',
                '-qscale:a', '2',
                '-y',
                mp3_path
            ]
            
            logger.info(f"Converting audio to MP3 format")
            process = subprocess.run(mp3_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"MP3 conversion completed")
            
            return mp3_path
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def transcribe_audio(self, mp3_path):
        """Transcribe audio using Google Cloud Speech-to-Text."""
        logger.info(f"Starting audio transcription for {mp3_path}")
        try:
            # Use Google Cloud Speech-to-Text
            key_path = "/Users/Shamanth/ad analyzr nov 2024/service-account-key.json"
            client = speech.SpeechClient.from_service_account_file(key_path)
            
            with open(mp3_path, "rb") as audio_file:
                content = audio_file.read()
            
            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.MP3,
                language_code="en-US"
            )
            
            response = client.recognize(config=config, audio=audio)
            
            # Combine transcribed text
            transcript = ""
            for result in response.results:
                transcript += result.alternatives[0].transcript
            
            logger.info(f"Transcription successful, length: {len(transcript)}")
            
            # Track approximate costs
            self._calculate_cost(
                model='gemini-2.0-flash',
                input_tokens=len(transcript) // 4,
                output_tokens=0,
                num_images=0
            )
            
            return transcript
        except Exception as e:
            logger.error(f"Error in transcription: {str(e)}")
            logger.error(traceback.format_exc())
            return f"Error transcribing audio: {str(e)}"
    
    def proofread_transcript(self, transcript):
        """Proofread transcript using Gemini."""
        if not transcript or transcript.strip() == "":
            return ""
        
        try:
            prompt = f"""This is a transcript from a marketing video that may or may not have spoken dialogue.

IMPORTANT INSTRUCTIONS:
1. If the transcript is empty or contains minimal content, DO NOT add any content. Return exactly what was provided.
2. If the transcript contains actual spoken content, format it properly with punctuation and speaker labels if needed. If there are extraneous and seemingly background contents, ignore them (eg - background music, sound effects, or noise).
3. DO NOT invent or hallucinate any dialogue that wasn't in the original transcript.
4. DO NOT add descriptions of signing, visual elements, or actions unless explicitly mentioned in the transcript.
5. If the transcript seems unrelated to the video content, return an empty string.

Original transcript:
{transcript}"""
            
            if self.gemini_model:
                response = retry_with_backoff(
                    lambda: self.gemini_model.generate_content(
                        prompt,
                        generation_config=GenerationConfig(
                            temperature=0.3,
                            top_p=0.95,
                        )
                    ),
                    max_retries=5,
                    initial_delay=10
                )
                
                self._calculate_cost(
                    model='gemini-2.0-flash',
                    input_tokens=len(prompt) // 4,
                    output_tokens=len(response.text) // 4,
                    num_images=0
                )
                
                return response.text.strip()
            else:
                logger.warning("Gemini model not available, returning original transcript")
                return transcript
        except Exception as e:
            logger.error(f"Error proofreading transcript: {str(e)}")
            traceback.print_exc()
            return transcript

    def _get_video_duration(self, video_path):
        """Get video duration in seconds."""
        try:
            video = cv2.VideoCapture(video_path)
            if not video.isOpened():
                return 0
            fps = video.get(cv2.CAP_PROP_FPS)
            total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            video.release()
            return duration
        except Exception as e:
            logger.warning(f"Error getting video duration: {e}")
            return 0

    def analyze_video_natively(self, video_path):
        """
        Analyze video natively using Vertex AI Gemini.
        Handles videos up to 2GB (Vertex AI limit).
        Uses Part.from_data() for <20MB, Part.from_uri() for larger files.

        Returns:
            List of scene dictionaries with timestamp and description
        """
        if not self.prompt_manager or not self.gemini_model:
            logger.info("Prompt manager or Gemini model not available, skipping native analysis")
            return []

        try:
            # Get video metadata
            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            duration = self._get_video_duration(video_path)

            logger.info(f"Native analysis: {file_size_mb:.1f}MB, {duration:.1f}s duration")

            # Validate duration (max 3 minutes)
            if duration > 180:
                logger.warning(f"Video too long ({duration:.1f}s), max 180s. Skipping native analysis.")
                return []

            # STRATEGY 1: Small files (<20MB) - Use Part.from_data()
            if file_size_mb < 20:
                logger.info("Using Part.from_data() for small file")
                with open(video_path, 'rb') as f:
                    video_bytes = f.read()
                video_part = Part.from_data(data=video_bytes, mime_type="video/mp4")

            # STRATEGY 2: Large files (20MB+) - Try Part.from_uri() with file://
            else:
                logger.info("Testing Part.from_uri() for large file...")
                try:
                    abs_path = os.path.abspath(video_path)
                    video_part = Part.from_uri(uri=f"file://{abs_path}", mime_type="video/mp4")
                    logger.info("✅ file:// URI supported!")
                except Exception as uri_error:
                    logger.warning(f"⚠️ file:// URI not supported: {uri_error}")
                    logger.info("Fallback: Skipping native analysis for large file (would need GCS)")
                    return []

            # Load prompt from external file
            prompt = self.prompt_manager.get_prompt('native_video_timeline')

            logger.info("Sending video to Gemini for native analysis...")
            response = retry_with_backoff(
                lambda: self.gemini_model.generate_content(
                    [video_part, prompt],
                    generation_config={'temperature': 0.2}  # Low temp for consistent format
                ),
                max_retries=5,
                initial_delay=10
            )

            # Parse timeline from response
            scenes = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                # Skip headers, examples, and non-data lines
                if ':' in line and not line.startswith(('#', 'Example', 'Focus', '-')):
                    try:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            ts_str = parts[0].strip()
                            desc = parts[1].strip()

                            # Extract numeric timestamp (handles "0.0s" or "0.0" or "0:00")
                            ts_match = re.search(r'(\d+\.?\d*)', ts_str)
                            if ts_match:
                                timestamp = float(ts_match.group(1))
                                scenes.append({
                                    'timestamp': timestamp,
                                    'description': f"[NATIVE] {desc}"  # Tag for tracking
                                })
                    except Exception as parse_error:
                        logger.debug(f"Skipping line (parse error): {line}")
                        continue

            logger.info(f"✅ Native analysis: {len(scenes)} scenes extracted")
            return scenes

        except Exception as e:
            logger.warning(f"Native video analysis failed: {e}", exc_info=True)
            return []  # Graceful fallback to frame-based only

    def reconcile_scenes_with_ai(self, frame_scenes, native_scenes):
        """
        Intelligently combine frame-based and native video scene descriptions using AI.

        Strategy:
        - Both sources describe the same video from different perspectives
        - Frame scenes: Detailed visual snapshots at sampled timestamps
        - Native scenes: Flow, transitions, pacing across entire video
        - Use AI to create comprehensive descriptions combining both

        Args:
            frame_scenes: Scenes from analyze_frames_batch() - list of dicts with 'timestamp' and 'description'
            native_scenes: Scenes from analyze_video_natively() - list of dicts with 'timestamp' and 'description'

        Returns:
            Combined scene timeline with enriched descriptions
        """
        if not native_scenes:
            logger.info("No native scenes to combine, using frame-based only")
            return frame_scenes

        if not self.prompt_manager or not self.gemini_model:
            logger.info("Prompt manager or Gemini model not available, using frame-based only")
            return frame_scenes

        # Create a narrative context from all native scenes
        native_context = " ".join([s['description'] for s in native_scenes])

        enriched_scenes = []

        for frame_scene in frame_scenes:
            try:
                # Load external prompt
                prompt = self.prompt_manager.get_prompt('combine_scene_descriptions', {
                    'frame_description': frame_scene['description'],
                    'native_description': native_context
                })

                # Use AI to combine descriptions with retry
                response = retry_with_backoff(
                    lambda: self.gemini_model.generate_content(
                        prompt,
                        generation_config={
                            'temperature': 0.1,
                            'max_output_tokens': 200
                        }
                    ),
                    max_retries=5,
                    initial_delay=10
                )

                enriched_scenes.append({
                    'timestamp': frame_scene['timestamp'],
                    'description': response.text.strip()
                })

            except Exception as e:
                logger.warning(f"Error combining scene at {frame_scene['timestamp']}: {e}")
                # Fallback: Use original frame description
                enriched_scenes.append(frame_scene)

        logger.info(f"Successfully enriched {len(enriched_scenes)} scenes with native context")
        return enriched_scenes

    def analyze_video_natively_with_timeout(self, video_path, timeout_seconds=300):
        """
        Wrapper for analyze_video_natively() with timeout protection.
        
        Args:
            video_path: Path to video file
            timeout_seconds: Maximum seconds to wait (default: 300 = 5 minutes)
            
        Returns:
            List of scene dictionaries, or empty list on timeout
            
        Raises:
            TimeoutError: If analysis exceeds timeout_seconds
        """
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Native video analysis exceeded {timeout_seconds} second timeout")
        
        # Set up timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        
        try:
            result = self.analyze_video_natively(video_path)
            signal.alarm(0)  # Cancel alarm
            return result
        except TimeoutError:
            signal.alarm(0)  # Cancel alarm
            logger.warning(f"⚠️ Native video analysis timed out after {timeout_seconds}s")
            raise
        finally:
            # Restore original handler
            signal.signal(signal.SIGALRM, old_handler)
