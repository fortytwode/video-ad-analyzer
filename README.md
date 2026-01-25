# Video Ad Analyzer

Analyze marketing videos and images using Google's Gemini AI to extract marketing dimensions, hooks, messaging patterns, and strategic insights.

## What It Does

The analyzer processes video ads and extracts:

- **Hooks**: Opening hooks (visual, spoken, text overlays)
- **Social Proof**: Testimonials, reviews, authority signals
- **Pain Points**: Problems being addressed
- **Benefits**: Value propositions and outcomes
- **CTAs**: Calls to action and their placement
- **Urgency**: Scarcity and time pressure tactics
- **Offers**: Pricing, deals, bundles
- **Objection Handling**: How concerns are addressed
- **Emotional Triggers**: Emotional appeals used
- **Visual Style**: Design and aesthetic choices
- **Messaging Sequence**: How the message unfolds

## Requirements

- Python 3.9+
- Google Cloud account with Vertex AI enabled
- Service account with Vertex AI permissions

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/YOUR_USERNAME/video-ad-analyzer.git
cd video-ad-analyzer
pip install -r requirements.txt
```

### 2. Set Up Google Cloud

1. Create a Google Cloud project at [console.cloud.google.com](https://console.cloud.google.com)

2. Enable the Vertex AI API:
   ```
   APIs & Services > Enable APIs > Search "Vertex AI" > Enable
   ```

3. Create a service account:
   ```
   IAM & Admin > Service Accounts > Create Service Account
   ```
   - Name: `video-analyzer`
   - Role: `Vertex AI User`

4. Download the JSON key:
   ```
   Service Account > Keys > Add Key > Create new key > JSON
   ```

### 3. Configure

```bash
cp config.example.py config.py
```

Edit `config.py`:

```python
SERVICE_ACCOUNT_PATH = "/path/to/your-service-account.json"
PROJECT_ID = "your-project-id"
```

### 4. Run Analysis

```bash
# Analyze a single video
python analyze.py --video path/to/ad.mp4

# Analyze all videos in a directory
python analyze.py --directory path/to/ads/

# Limit batch size
python analyze.py --directory path/to/ads/ --max 10
```

## Output

Results are saved to `analysis_output/` (configurable) as JSON files:

```
analysis_output/
└── 2024-01-15_10-30-45/
    ├── consolidated.json      # All dimensions in one file
    ├── hooks.json
    ├── social_proof.json
    ├── pain_points.json
    ├── benefits.json
    ├── cta.json
    └── ...
```

### Example Output

```json
{
  "hooks": {
    "visual_hook": {
      "description": "Close-up of frustrated person looking at phone",
      "timestamp": "0:00-0:03",
      "effectiveness": "High - immediately relatable emotion"
    },
    "spoken_hook": {
      "text": "Tired of apps that don't actually work?",
      "tone": "Empathetic, slightly frustrated"
    },
    "text_hook": {
      "text": "STOP SCROLLING",
      "style": "Bold white text, red background"
    }
  }
}
```

## Configuration Options

See `config.example.py` for all options:

| Option | Description | Default |
|--------|-------------|---------|
| `DEFAULT_MODEL` | Gemini model to use | `gemini-2.0-flash` |
| `API_CALL_DELAY` | Seconds between API calls | `30` |
| `NATIVE_ANALYSIS_TIMEOUT` | Max time for video analysis | `300` |
| `RUN_STRATEGIC_ANALYSIS` | Run pattern aggregation | `True` |

## Supported Formats

**Video**: `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`

**Image**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`

## Cost Estimate

Using `gemini-2.0-flash` (recommended):
- ~$0.01-0.03 per video (depending on length)
- ~$0.005 per image

## Troubleshooting

### "Service account file not found"

Make sure `SERVICE_ACCOUNT_PATH` in `config.py` points to your downloaded JSON key file.

### "Permission denied" errors

Ensure your service account has the `Vertex AI User` role.

### Rate limit errors

Increase `API_CALL_DELAY` in `config.py` (default: 30 seconds).

### Video processing fails

Install ffmpeg for audio extraction:
```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt install ffmpeg
```

## License

MIT License - Use freely in your projects.
