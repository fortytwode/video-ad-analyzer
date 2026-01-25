"""
Marketing analysis module.

Handles marketing dimension analysis using external prompts.
"""

import json
import logging
import time
import hashlib
import os
import re
import traceback
from vertexai.generative_models import GenerativeModel, GenerationConfig
from google.api_core import exceptions as google_exceptions
from ..models import MarketingAnalysis, MarketingDimension

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


class MarketingAnalyzer:
    """Analyzes marketing dimensions using dynamic prompt templates."""
    
    def __init__(self, gemini_model=None, prompt_manager=None):
        """
        Initialize MarketingAnalyzer.
        
        Args:
            gemini_model: Gemini model instance for content generation
            prompt_manager: PromptManager instance for loading templates
        """
        self.gemini_model = gemini_model
        self.prompt_manager = prompt_manager
        
        # Cost tracking
        self.cost_tracking = {
            'gemini-2.0-flash': {'calls': 0, 'tokens': {'input': 0, 'output': 0}, 'cost': 0},
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
        
        total_cost = token_cost
        self.cost_tracking[model]['cost'] += total_cost
        
        logger.debug(f"Cost: {model} - ${total_cost:.6f} (tokens: {input_tokens}/{output_tokens})")
        
        return total_cost
    
    def _format_text_entries(self, text_timeline):
        """Format text timeline entries for prompt injection."""
        if not text_timeline:
            return "No text overlays detected"
        
        formatted = []
        for entry in text_timeline:
            timestamp = entry.get('at', 0)
            text_items = entry.get('text', [])
            
            if isinstance(text_items, list):
                text_str = " ".join([t.strip() for t in text_items if t and t.strip()])
            else:
                text_str = text_items.strip() if text_items else ""
            
            if text_str:
                formatted.append(f"At {timestamp:.2f}s: {text_str}")
        
        return "\n".join(formatted) if formatted else "No text overlays detected"
    
    def _get_cleaned_json(self, text):
        """Parse JSON from API response with optimal balance of simplicity and robustness."""
        text = text.strip()
        if not text:
            logger.warning("Empty response from API")
            return {}
        
        logger.debug(f"Raw JSON response (truncated): {text[:150]}...")
        
        # STEP 1: Direct parsing
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # STEP 2: Handle markdown code blocks
        if "```" in text:
            code_blocks = re.findall(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
            for block in code_blocks:
                try:
                    return json.loads(block.strip())
                except:
                    continue
        
        # STEP 3: Balanced delimiter extraction
        def extract_balanced(text, open_char, close_char):
            """Extract content between balanced delimiters"""
            if open_char not in text or close_char not in text:
                return None
            
            start = text.find(open_char)
            if start == -1:
                return None
            
            level = 0
            for i in range(start, len(text)):
                if text[i] == open_char:
                    level += 1
                elif text[i] == close_char:
                    level -= 1
                    if level == 0:
                        return text[start:i+1]
            return None
        
        # Try array extraction first
        json_array = extract_balanced(text, '[', ']')
        if json_array:
            try:
                logger.debug(f"Extracted JSON array: {json_array[:100]}...")
                return json.loads(json_array)
            except:
                pass
        
        # Try object extraction next
        json_object = extract_balanced(text, '{', '}')
        if json_object:
            try:
                logger.debug(f"Extracted JSON object: {json_object[:100]}...")
                return json.loads(json_object)
            except:
                # If it looks like an array element, wrap it
                if json_object.startswith('{') and json_object.endswith('}'):
                    try:
                        return json.loads('[' + json_object + ']')
                    except:
                        pass
        
        logger.warning("All JSON parsing attempts failed")
        return {}
    
    def analyze_marketing_dimensions(self, raw_content, basic_analysis, summary=None, is_image=False):
        """Analyze all marketing dimensions based on raw content and summary.
        
        Args:
            raw_content: Dict with transcript, timeline, etc.
            basic_analysis: Frame descriptions
            summary: Optional summary text
            is_image: If True, skips temporal processing dimensions (images have no temporal reconciliation needs)
        """
        analysis = MarketingAnalysis()
        
        try:
            # Set metadata
            transcript_text = raw_content.get("transcript", "") or ""
            analysis.metadata["video_id"] = hashlib.md5(transcript_text.encode()).hexdigest()
            analysis.metadata["filename"] = os.path.basename(raw_content.get("video_path", "unknown"))
            analysis.metadata["analysis_time"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            analysis.metadata["duration"] = raw_content.get("duration", "unknown")
            
            # Add summary to metadata if available
            if summary:
                analysis.metadata["summary"] = summary
            
            # Early return if no content
            if not transcript_text and not basic_analysis:
                logger.warning("No transcript or basic analysis available")
                return analysis
            
            # Prepare variables for prompt substitution
            text_timeline_formatted = self._format_text_entries(raw_content.get("text_timeline", []))
            scenes_formatted = json.dumps([{"timestamp": f.get("timestamp", 0), "description": f.get("description", "")} 
                                          for f in basic_analysis if f.get("description")]) if basic_analysis else "[]"
            
            # Extract early content for hooks
            words = transcript_text.split() if transcript_text else []
            early_words = ' '.join(words[:min(30, len(words))]) if words else ""
            early_frames = [f for f in basic_analysis if f.get("timestamp", 0) <= 5.0] if basic_analysis else []
            early_frames_formatted = json.dumps([f.get("description", "") for f in early_frames])
            
            variables = {
                "transcript": transcript_text,
                "text_timeline": text_timeline_formatted,
                "scenes": scenes_formatted,
                "early_words": early_words,
                "early_frames": early_frames_formatted,
                "frame_count": str(len(basic_analysis) if basic_analysis else 0)
            }
            
            # Analyze ALL dimensions dynamically from prompts
            # EXCLUDE Part 3 strategic analysis prompts (those run separately in Part 3)
            PART3_PROMPTS = {'formula_generation', 'pattern_normalization'}
            
            # EXCLUDE technical dimensions for images (no temporal reconciliation needed)
            TECHNICAL_DIMENSIONS = {
                'frame_analysis', 'native_video_timeline',
                'combine_scene_descriptions', 'extract_text_from_scenes',
                'reconcile_text_sources'
            }
            
            # Determine which dimensions to skip based on content type
            skip_dimensions = PART3_PROMPTS.copy()
            
            # Skip technical dimensions for ALL content (not consumed by Part 3)
            # Technical PROCESSING still happens in video_extractor
            # These prompts only document that processing and are currently failing
            skip_dimensions.update(TECHNICAL_DIMENSIONS)
            logger.info(f"{'Image' if is_image else 'Video'} mode: Analyzing marketing dimensions only")
            
            if self.prompt_manager:
                # Count total dimensions for rate limiting (excluding Part 3)
                total_dimensions = sum(
                    len([t for t in templates.keys() if t not in PART3_PROMPTS])
                    for templates in self.prompt_manager.loaded_prompts.values()
                )
                dimension_count = 0
                
                for file_key, templates in self.prompt_manager.loaded_prompts.items():
                    for template_name in templates.keys():
                        # Skip dimensions not relevant to this content type
                        if template_name in skip_dimensions:
                            logger.debug(f"Skipping dimension: {template_name}")
                            continue
                        
                        dimension_count += 1
                        try:
                            logger.info(f"Analyzing dimension: {template_name}")
                            
                            # Get formatted prompt
                            prompt = self.prompt_manager.get_prompt(template_name, variables)
                            
                            # Call Gemini with retry logic
                            response = retry_with_backoff(
                                lambda: self.gemini_model.generate_content(prompt),
                                max_retries=5,
                                initial_delay=10
                            )
                            result = self._get_cleaned_json(response.text)
                            
                            # Normalize elements to array
                            if "elements" in result and isinstance(result["elements"], dict):
                                result["elements"] = [result["elements"]]

                            # Create MarketingDimension object
                            dimension = MarketingDimension()

                            # KEEP ONLY THE MOST PROMINENT ELEMENT (first one)
                            # Gemini returns elements in order of importance
                            elements = result.get("elements", [])
                            if isinstance(elements, list) and len(elements) > 0:
                                dimension.elements = [elements[0]]  # Keep only first (most prominent)
                            else:
                                dimension.elements = []

                            dimension.context = result.get("context", "")
                            dimension.salience_score = result.get("salience_score")  # Extract salience score

                            analysis.dimensions[template_name] = dimension
                            salience_str = f" [salience: {dimension.salience_score}]" if dimension.salience_score is not None else ""
                            logger.info(f"✓ {template_name}: {len(dimension.elements)} element (most prominent){salience_str}")
                            
                            # Add delay between dimensions to avoid rate limits (except for last dimension)
                            if dimension_count < total_dimensions:
                                logger.debug(f"Waiting 5 seconds before next dimension...")
                                time.sleep(5)
                            
                        except Exception as e:
                            logger.error(f"✗ {template_name}: {e}")
                            dimension = MarketingDimension()
                            dimension.elements = []
                            dimension.context = f"Error: {str(e)}"
                            analysis.dimensions[template_name] = dimension
            else:
                logger.error("PromptManager not initialized - skipping dimension analysis")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in marketing analysis: {str(e)}")
            traceback.print_exc()
            return analysis
    
    def generate_summary(self, timeline, text_timeline):
        """Generate a summary using both scene analysis and text timeline."""
        try:
            # Extract timeline entries
            timeline_entries = timeline.get('timeline', [])
            
            # Combine scene analysis with text timeline
            combined_timeline = []
            for entry in timeline_entries:
                timestamp = entry.get('at', 0)
                text_items = entry.get('text', [])
                scene = entry.get('scene')
                
                # Handle text items
                if isinstance(text_items, list):
                    text_str = " ".join([t.strip() for t in text_items if t and t.strip()])
                else:
                    text_str = text_items.strip() if text_items else ""
                
                if text_str:
                    combined_timeline.append(f"At {timestamp:.2f}s: {text_str}")
                
                if scene:
                    combined_timeline.append(f"[Scene]: {scene}")
                
                combined_timeline.append("\n")
            
            timeline_text = "\n".join(combined_timeline)
            
            # Create the prompt
            prompt = f"""Analyze this video content and create a structured summary:

Timeline:
{timeline_text}

Please provide a summary that includes:
Product/App: The specific product or app being showcased
Key Features: Main features or benefits demonstrated
Target Audience: Who this video is made for
Call to Action: What viewers are asked to do

Focus on the actual content shown and text overlays used."""
            
            # Generate content using Gemini model with retry logic
            response = retry_with_backoff(
                lambda: self.gemini_model.generate_content(prompt),
                max_retries=5,
                initial_delay=10
            )
            
            self._calculate_cost(
                model='gemini-2.0-flash',
                input_tokens=response.usage_metadata.prompt_token_count,
                output_tokens=response.usage_metadata.total_token_count
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            traceback.print_exc()
            return f"Error generating summary: {str(e)}"
