"""
Video Analysis Package

A modular video marketing analysis system that extracts and analyzes marketing
dimensions from video content using Google's Gemini AI.

Main Components:
- VideoExtractor: Handles video content extraction (frames, audio, text)
- MarketingAnalyzer: Analyzes marketing dimensions using AI
- PromptManager: Manages external prompt templates

Usage:
    from video_analysis import analyze_video, initialize_gemini

    model = initialize_gemini()
    result = analyze_video('path/to/video.mp4', model)
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

from .local_media import selected_media
from .models import MarketingAnalysis, MarketingDimension, HookAnalysis
from .core import VideoExtractor, MarketingAnalyzer, PromptManager

__version__ = '1.0.0'
__all__ = [
    'analyze_video',
    'initialize_gemini',
    'VideoExtractor',
    'MarketingAnalyzer',
    'PromptManager',
    'MarketingAnalysis',
    'MarketingDimension',
    'HookAnalysis',
]

logger = logging.getLogger(__name__)

# Try to load config
def _load_config():
    """Load configuration from config.py"""
    try:
        # Try to import from parent directory
        config_path = Path(__file__).parent.parent.parent / "config.py"
        if config_path.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location("config", config_path)
            config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config)
            return config
    except Exception as e:
        logger.warning(f"Could not load config.py: {e}")
    return None

_config = _load_config()


def initialize_gemini(service_account_path=None, project_id=None, location=None, model_name=None):
    """
    Initialize Gemini model for video analysis.

    Args:
        service_account_path: Path to service account JSON file (or set in config.py)
        project_id: Google Cloud project ID (or set in config.py)
        location: Google Cloud location (or set in config.py)
        model_name: Gemini model to use (or set in config.py)

    Returns:
        Gemini model instance
    """
    # Use config values as defaults
    if _config:
        service_account_path = service_account_path or getattr(_config, 'SERVICE_ACCOUNT_PATH', None)
        project_id = project_id or getattr(_config, 'PROJECT_ID', None)
        location = location or getattr(_config, 'LOCATION', 'us-central1')
        model_name = model_name or getattr(_config, 'DEFAULT_MODEL', 'gemini-2.0-flash')
    else:
        location = location or 'us-central1'
        model_name = model_name or 'gemini-2.0-flash'

    # Validate required parameters
    if not service_account_path:
        raise ValueError(
            "service_account_path is required. "
            "Either pass it as an argument or set SERVICE_ACCOUNT_PATH in config.py"
        )

    if not project_id:
        raise ValueError(
            "project_id is required. "
            "Either pass it as an argument or set PROJECT_ID in config.py"
        )

    # Verify service account file exists
    if not os.path.exists(service_account_path):
        raise FileNotFoundError(f"Service account file not found: {service_account_path}")

    # Set environment variables
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = location

    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel

        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)

        # Create Gemini model instance
        gemini_model = GenerativeModel(model_name)
        logger.info(f"Initialized Gemini model: {model_name}")

        return gemini_model
    except ImportError:
        raise ImportError(
            "google-cloud-aiplatform is required. "
            "Install with: pip install google-cloud-aiplatform"
        )
    except Exception as e:
        logger.error(f"Error initializing Gemini API: {str(e)}")
        raise


def analyze_video(video_path, gemini_model=None, prompt_manager=None, output_dir=None,
                  temp_dir=None, skip_save=False, model_name=None, api_delay=None, *, directory_fd=None):
    """
    Main analysis function for video or image.

    Args:
        video_path: Path to video or image file
        gemini_model: Pre-initialized Gemini model instance
        prompt_manager: Pre-initialized PromptManager instance
        output_dir: Optional output directory (if None, uses config or creates timestamped dir)
        temp_dir: Temporary directory for processing files
        skip_save: If True, skip saving individual JSON files (for batch mode)
        model_name: Gemini model to use if gemini_model is None
        api_delay: Delay between API calls in seconds (helps with rate limits)

    Returns:
        tuple: (raw_content dict, marketing_analysis object)
    """
    temp_dir = temp_dir or getattr(_config, "TEMP_DIR", "temp_videos")
    os.makedirs(temp_dir, exist_ok=True)
    with selected_media(video_path, directory_fd=directory_fd, temp_dir=temp_dir) as local_path:
        return _analyze_selected_media(
            local_path, os.fspath(video_path), gemini_model, prompt_manager,
            output_dir, temp_dir, skip_save, model_name, api_delay,
        )


def _analyze_selected_media(video_path, original_path, gemini_model, prompt_manager,
                            output_dir, temp_dir, skip_save, model_name, api_delay):
    import time
    import json

    # Load config defaults
    if _config:
        temp_dir = temp_dir or getattr(_config, 'TEMP_DIR', 'temp_videos')
        output_dir = output_dir or getattr(_config, 'OUTPUT_DIR', 'analysis_output')
        api_delay = api_delay if api_delay is not None else getattr(_config, 'API_CALL_DELAY', 30)
    else:
        temp_dir = temp_dir or 'temp_videos'
        output_dir = output_dir or 'analysis_output'
        api_delay = api_delay if api_delay is not None else 30

    try:
        # Initialize Gemini if not provided
        if gemini_model is None:
            gemini_model = initialize_gemini(model_name=model_name)

        # Initialize PromptManager if not provided
        if prompt_manager is None:
            prompts_dir = os.path.join(os.path.dirname(__file__), "..", "prompts")
            prompt_manager = PromptManager(prompts_dir)
            logger.info(f"Loaded {len(prompt_manager.loaded_prompts)} prompt template files")

        # Create directories
        os.makedirs(temp_dir, exist_ok=True)

        if not skip_save:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_dir = os.path.join(output_dir, timestamp)
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Output directory: {output_dir}")

        # Initialize components
        extractor = VideoExtractor(gemini_model=gemini_model, temp_dir=temp_dir, prompt_manager=prompt_manager)
        analyzer = MarketingAnalyzer(gemini_model=gemini_model, prompt_manager=prompt_manager)

        logger.info(f"Starting analysis of {video_path}")

        # Check if this is an image
        is_image = extractor._is_image_file(video_path)

        # Extract audio and transcribe (skip for images)
        transcript = None
        if not is_image:
            audio_path = video_path + ".wav"
            mp3_path = extractor.extract_audio(video_path, audio_path)

            if mp3_path:
                try:
                    transcript = extractor.transcribe_audio(mp3_path)
                    if transcript:
                        transcript = extractor.proofread_transcript(transcript)
                except Exception as e:
                    logger.error(f"Error in transcription: {str(e)}")
                finally:
                    # Clean up audio files
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                    if mp3_path and os.path.exists(mp3_path):
                        os.remove(mp3_path)

            if api_delay > 0:
                logger.info(f"Waiting {api_delay}s before vision analysis...")
                time.sleep(api_delay)
        else:
            logger.info("Skipping audio extraction for image file")

        # Extract content (handles both videos and images)
        logger.info("Extracting content...")
        vision_frames, vision_timestamps, text_timeline = extractor.extract_content(video_path)

        if api_delay > 0:
            logger.info(f"Waiting {api_delay}s before analyzing frames...")
            time.sleep(api_delay)

        # Analyze frames
        logger.info("Analyzing frames...")
        scene_descriptions_list, scene_descriptions_dict = extractor.analyze_frames_batch(
            vision_frames, vision_timestamps, text_timeline
        )

        # Native video analysis (skip for images)
        if not is_image:
            logger.info("Enriching scenes with native video analysis...")
            try:
                timeout = getattr(_config, 'NATIVE_ANALYSIS_TIMEOUT', 300) if _config else 300
                native_scenes = extractor.analyze_video_natively_with_timeout(
                    video_path,
                    timeout_seconds=timeout
                )
                if native_scenes:
                    scene_descriptions_list = extractor.reconcile_scenes_with_ai(
                        scene_descriptions_list, native_scenes
                    )
                    scene_descriptions_dict = {
                        scene['timestamp']: scene['description']
                        for scene in scene_descriptions_list
                    }
                    logger.info(f"Enriched timeline: {len(scene_descriptions_list)} scenes")
            except Exception as e:
                logger.warning(f"Native video analysis failed: {e} - continuing anyway")

        if api_delay > 0:
            logger.info(f"Waiting {api_delay}s before creating timeline...")
            time.sleep(api_delay)

        # Create combined timeline
        timeline = []
        for entry in text_timeline:
            timeline.append(entry)

        for timestamp, scene in scene_descriptions_dict.items():
            timeline.append({'at': timestamp, 'scene': scene})

        timeline.sort(key=lambda x: x['at'])

        # Prepare raw_content
        raw_content = {
            "video_path": original_path,
            "duration": "00:00" if is_image else _get_video_duration(video_path),
            "transcript": transcript,
            "text_timeline": timeline
        }

        # Generate summary
        logger.info("Generating video summary...")
        timeline_data = {"timeline": timeline}
        summary = analyzer.generate_summary(timeline_data, text_timeline)
        raw_content["summary"] = summary

        if api_delay > 0:
            logger.info(f"Waiting {api_delay}s before analyzing marketing dimensions...")
            time.sleep(api_delay)

        # Analyze marketing dimensions
        logger.info("Analyzing marketing dimensions...")
        marketing_analysis = analyzer.analyze_marketing_dimensions(
            raw_content, scene_descriptions_list, summary, is_image=is_image
        )

        # Save results
        if not skip_save:
            logger.info("Saving results...")
            _save_analysis_results(marketing_analysis, output_dir)

        logger.info("Analysis complete!")

        return raw_content, marketing_analysis

    except Exception as e:
        logger.error(f"Error in analyze_video: {str(e)}")
        raise


def _get_video_duration(video_path):
    """Get video duration using OpenCV."""
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return "unknown"

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0

        cap.release()

        return f"{int(duration // 60):02d}:{int(duration % 60):02d}"
    except Exception as e:
        logger.warning(f"Error getting video duration: {str(e)}")
        return "unknown"


def _save_analysis_results(marketing_analysis, output_dir):
    """Save marketing analysis results to JSON files."""
    import json

    saved_count = 0
    for dimension_name, dimension_data in marketing_analysis.dimensions.items():
        try:
            output_file = os.path.join(output_dir, f"{dimension_name}.json")

            if hasattr(dimension_data, 'to_dict'):
                json_data = dimension_data.to_dict()
            else:
                json_data = {
                    "elements": dimension_data.elements if hasattr(dimension_data, 'elements') else [],
                    "context": dimension_data.context if hasattr(dimension_data, 'context') else ""
                }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)

            saved_count += 1
        except Exception as e:
            logger.error(f"Failed to save {dimension_name}.json: {e}")

    # Save consolidated JSON
    try:
        consolidated_file = os.path.join(output_dir, "consolidated.json")
        consolidated_data = marketing_analysis.to_dict()
        with open(consolidated_file, 'w', encoding='utf-8') as f:
            json.dump(consolidated_data, f, indent=2, ensure_ascii=False)
        saved_count += 1
    except Exception as e:
        logger.error(f"Failed to save consolidated.json: {e}")

    logger.info(f"Saved {saved_count} JSON files to {output_dir}")
