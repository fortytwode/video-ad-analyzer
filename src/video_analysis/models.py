"""
Data models for video marketing analysis.

This module defines the data structures used throughout the video analysis pipeline.
"""

class MarketingDimension:
    """Base class for marketing dimensions analysis"""
    def __init__(self):
        self.elements = {}  # Main analysis elements
        self.impact = ""    # Impact description
        self.context = ""   # Contextual analysis
        self.confidence = 0.0
        self.salience_score = None  # Marketing impact score (0.0-1.0)

    def to_dict(self):
        result = {
            "elements": self.elements,
            # "impact": self.impact,
            "context": self.context
        }
        # Include salience_score if it exists
        if self.salience_score is not None:
            result["salience_score"] = self.salience_score
        return result

class HookAnalysis(MarketingDimension):
    """Analyzes spoken and visual hooks"""
    def __init__(self):
        super().__init__()
        self.elements = {
            "exact_hook": "",      # Primary field - exact spoken words or visual elements
            "first_impression": "",
            "hook_type": "",
        }

# Removed MessageSequencing class - narrative_flow now uses base MarketingDimension

class MarketingAnalysis:
    """Container for all marketing dimensions analysis"""
    def __init__(self):
        self.metadata = {
            "video_id": "",
            "filename": "",
            "analysis_time": "",
            "duration": ""
        }
        # Dimensions will be dynamically populated from prompt templates
        # Default initialization with new framework dimensions only
        self.dimensions = {
            # Hook dimensions (3)
            "hooks_spoken": HookAnalysis(),
            "hooks_visual": HookAnalysis(),
            "hooks_text": HookAnalysis(),
            # New framework dimensions (8)
            "problem": MarketingDimension(),
            "aspiration_transformation": MarketingDimension(),
            "credibility": MarketingDimension(),
            "urgency": MarketingDimension(),
            "visual_format": MarketingDimension(),
            "narrative_flow": MarketingDimension(),
            "emotion": MarketingDimension(),
            "target_audience": MarketingDimension(),
        }

    def to_dict(self):
        return {
            "metadata": self.metadata,
            "dimensions": {k: (v.to_dict() if hasattr(v, 'to_dict') else v) for k, v in self.dimensions.items()}
        }
