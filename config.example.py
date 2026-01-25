"""
Video Ad Analyzer Configuration

Copy this file to config.py and customize for your setup.

Requirements:
1. Google Cloud account with Vertex AI enabled
2. Service account with Vertex AI permissions
3. Python 3.9+ with required packages (see requirements.txt)
"""

# =============================================================================
# GOOGLE CLOUD CONFIGURATION
# =============================================================================

# Path to your Google Cloud service account JSON key file
# Create one at: https://console.cloud.google.com/iam-admin/serviceaccounts
SERVICE_ACCOUNT_PATH = "/path/to/your-service-account.json"

# Your Google Cloud project ID
PROJECT_ID = "your-project-id"

# Google Cloud region (us-central1 recommended for Vertex AI)
LOCATION = "us-central1"

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

# Gemini model to use for analysis
# Options:
#   - gemini-2.0-flash: Fast, cost-effective (recommended)
#   - gemini-1.5-pro: More capable, slower, higher cost
#   - gemini-1.5-flash: Balanced speed and capability
DEFAULT_MODEL = "gemini-2.0-flash"

# =============================================================================
# DIRECTORY CONFIGURATION
# =============================================================================

# Where to store temporary files during processing
TEMP_DIR = "temp_videos"

# Default output directory for analysis results
OUTPUT_DIR = "analysis_output"

# Default input directory for videos
INPUT_DIR = "videos_input"

# =============================================================================
# ANALYSIS SETTINGS
# =============================================================================

# Delay between API calls (seconds) - helps avoid rate limits
API_CALL_DELAY = 30

# Timeout for native video analysis (seconds)
NATIVE_ANALYSIS_TIMEOUT = 300

# Maximum videos to process in batch mode (None = no limit)
MAX_VIDEOS = None

# Whether to run strategic pattern analysis after video analysis
RUN_STRATEGIC_ANALYSIS = True

# =============================================================================
# VIDEO PROCESSING SETTINGS
# =============================================================================

# Supported video extensions
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}

# Supported image extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

# =============================================================================
# MARKETING DIMENSIONS
# =============================================================================
# The analyzer extracts these marketing dimensions from each video/image:

MARKETING_DIMENSIONS = [
    "hooks",              # Opening hooks (visual, spoken, text)
    "social_proof",       # Testimonials, reviews, authority signals
    "pain_points",        # Problems being addressed
    "benefits",           # Value propositions
    "cta",               # Calls to action
    "urgency",           # Scarcity and time pressure
    "offer",             # Pricing, deals, bundles
    "objection_handling", # Addressing concerns
    "emotional_triggers", # Emotional appeals
    "visual_style",       # Design and aesthetic
    "messaging_sequence", # Message flow and structure
]

# =============================================================================
# LOGGING
# =============================================================================

# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL = "INFO"

# Log format
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
