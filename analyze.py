#!/usr/bin/env python3
"""
Video Ad Analyzer - Analyze marketing videos using Gemini AI

Extracts and analyzes marketing dimensions from video ads including:
- Hooks (visual, spoken, text)
- Social proof and testimonials
- Pain points and benefits
- Calls to action
- Emotional triggers
- Visual style and messaging sequence

Usage:
    # Analyze a single video
    python analyze.py --video path/to/video.mp4

    # Analyze all videos in a directory
    python analyze.py --directory path/to/videos/

    # Specify output directory
    python analyze.py --video video.mp4 --output my_analysis

    # Use a specific model
    python analyze.py --video video.mp4 --model gemini-1.5-pro

Requirements:
    1. Copy config.example.py to config.py
    2. Add your Google Cloud service account credentials
    3. Install dependencies: pip install -r requirements.txt
"""

import argparse
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from config.py"""
    config_path = Path(__file__).parent / "config.py"

    if not config_path.exists():
        print("Error: config.py not found.")
        print()
        print("To get started:")
        print("  1. Copy config.example.py to config.py")
        print("  2. Add your Google Cloud credentials")
        print("  3. Run this script again")
        sys.exit(1)

    import importlib.util
    spec = importlib.util.spec_from_file_location("config", config_path)
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    return config


def get_video_files(directory):
    """Get all video/image files from a directory."""
    config = load_config()

    video_ext = getattr(config, 'VIDEO_EXTENSIONS', {'.mp4', '.mov', '.avi', '.mkv', '.webm'})
    image_ext = getattr(config, 'IMAGE_EXTENSIONS', {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'})
    all_ext = video_ext | image_ext

    files = []
    directory = Path(directory)

    for ext in all_ext:
        files.extend(directory.glob(f'*{ext}'))
        files.extend(directory.glob(f'*{ext.upper()}'))

    return sorted([str(f) for f in files])


def analyze_single(video_path, output_dir=None, model=None):
    """Analyze a single video."""
    from video_analysis import analyze_video, initialize_gemini
    from video_analysis.core import PromptManager

    config = load_config()

    # Initialize model
    logger.info(f"Initializing Gemini model: {model or config.DEFAULT_MODEL}")
    gemini_model = initialize_gemini(model_name=model)

    # Initialize prompt manager
    prompts_dir = Path(__file__).parent / "src" / "prompts"
    prompt_manager = PromptManager(str(prompts_dir))

    # Run analysis
    logger.info(f"Analyzing: {video_path}")
    raw_content, marketing_analysis = analyze_video(
        video_path,
        gemini_model=gemini_model,
        prompt_manager=prompt_manager,
        output_dir=output_dir,
        skip_save=False
    )

    return raw_content, marketing_analysis


def analyze_batch(directory, output_dir=None, model=None, max_videos=None):
    """Analyze all videos in a directory."""
    from video_analysis import analyze_video, initialize_gemini
    from video_analysis.core import PromptManager

    config = load_config()

    # Get video files
    video_files = get_video_files(directory)

    if not video_files:
        logger.error(f"No video/image files found in {directory}")
        return

    logger.info(f"Found {len(video_files)} files to analyze")

    # Apply limit
    if max_videos:
        video_files = video_files[:max_videos]
        logger.info(f"Limited to first {max_videos} files")

    # Initialize model
    logger.info(f"Initializing Gemini model: {model or config.DEFAULT_MODEL}")
    gemini_model = initialize_gemini(model_name=model)

    # Initialize prompt manager
    prompts_dir = Path(__file__).parent / "src" / "prompts"
    prompt_manager = PromptManager(str(prompts_dir))

    # Create output directory
    if output_dir is None:
        output_dir = getattr(config, 'OUTPUT_DIR', 'analysis_output')

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    batch_output_dir = os.path.join(output_dir, f"batch_analysis_{timestamp}")
    os.makedirs(batch_output_dir, exist_ok=True)
    os.makedirs(os.path.join(batch_output_dir, 'marketing'), exist_ok=True)

    # Process each file
    results = []
    for i, video_path in enumerate(video_files, 1):
        logger.info(f"\n[{i}/{len(video_files)}] Processing: {os.path.basename(video_path)}")

        try:
            raw_content, marketing_analysis = analyze_video(
                video_path,
                gemini_model=gemini_model,
                prompt_manager=prompt_manager,
                skip_save=True  # We'll save consolidated results
            )

            if raw_content and marketing_analysis:
                results.append({
                    'file': os.path.basename(video_path),
                    'raw_content': raw_content,
                    'marketing_analysis': marketing_analysis.to_dict()
                })
                logger.info(f"  Success!")
            else:
                logger.error(f"  Failed - no results returned")

        except Exception as e:
            logger.error(f"  Error: {e}")
            continue

    # Save consolidated results
    if results:
        consolidated_path = os.path.join(batch_output_dir, 'consolidated.json')
        with open(consolidated_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"\nSaved consolidated results to {consolidated_path}")

        # Save summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_files': len(video_files),
            'successful': len(results),
            'failed': len(video_files) - len(results),
            'output_directory': batch_output_dir
        }
        summary_path = os.path.join(batch_output_dir, 'summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"\n{'='*60}")
        logger.info(f"BATCH ANALYSIS COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Processed: {summary['successful']}/{summary['total_files']} files")
        logger.info(f"Output: {batch_output_dir}")
        logger.info(f"{'='*60}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Analyze marketing videos using Gemini AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --video ad.mp4                    # Analyze single video
  %(prog)s --directory ./ads/               # Analyze all videos in directory
  %(prog)s --video ad.mp4 --model gemini-1.5-pro  # Use specific model
  %(prog)s --directory ./ads/ --max 10      # Analyze first 10 videos
        """
    )

    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--video', '-v',
        help='Path to a single video or image file'
    )
    input_group.add_argument(
        '--directory', '-d',
        help='Path to directory containing videos/images'
    )

    # Other options
    parser.add_argument(
        '--output', '-o',
        help='Output directory for results'
    )
    parser.add_argument(
        '--model', '-m',
        help='Gemini model to use (default: from config.py)'
    )
    parser.add_argument(
        '--max',
        type=int,
        help='Maximum number of videos to analyze (for batch mode)'
    )

    args = parser.parse_args()

    # Verify config exists
    load_config()

    if args.video:
        # Single video analysis
        if not os.path.exists(args.video):
            print(f"Error: Video file not found: {args.video}")
            sys.exit(1)

        analyze_single(args.video, args.output, args.model)

    elif args.directory:
        # Batch analysis
        if not os.path.isdir(args.directory):
            print(f"Error: Directory not found: {args.directory}")
            sys.exit(1)

        analyze_batch(args.directory, args.output, args.model, args.max)


if __name__ == '__main__':
    main()
