# Scene Reconciliation Prompts

## Combine Scene Descriptions

### Template: combine_scene_descriptions
```
You are analyzing a marketing video. You have two descriptions of the same video from different analysis methods:

**Frame-based analysis:** {{frame_description}}

**Native video analysis:** {{native_description}}

These describe the same video but from different perspectives. The frame-based analysis provides detailed visual snapshots, while the native analysis captures flow, transitions, and pacing.

Combine these two descriptions into a single, comprehensive description that:
- Includes all important visual details from both sources
- Captures transitions and flow
- Maintains temporal accuracy
- Stays concise (2-3 sentences maximum)

Combined description:
```

## Extract Text from Scenes

### Template: extract_text_from_scenes
```
Analyze these scene descriptions from a video and extract any text overlays, signs, or written text that appear:

{{scenes}}

List each text element with its approximate timestamp. Only include text that is clearly visible in the descriptions.

Format as:
timestamp: text content

If no text is mentioned, return "No text overlays detected"
```

## Reconcile Text Sources

### Template: reconcile_text_sources
```
You have two sources of text from the same video:

SOURCE 1 (OCR - direct text detection):
{{ocr_texts}}

SOURCE 2 (Gemini Vision - text from scene descriptions):
{{gemini_texts}}

Reconcile these into a single, accurate timeline of text overlays. Prefer OCR for accuracy, but use Gemini Vision to fill gaps or provide context.

Format each entry as:
timestamp: text content

Return a deduplicated, chronological list.
```
