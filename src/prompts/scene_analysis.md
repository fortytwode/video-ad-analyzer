# Scene Analysis Prompts

## Frame Analysis

### Template: frame_analysis
```
Analyze these sequential frames from a marketing ad. For each frame:
1. What's happening in this specific moment?
2. Note any text overlays
3. Focus on changes from previous frame
4. Maximum 2 sentences per frame
5. Ignore static elements unless newly relevant

REQUIRED FORMAT: For each frame, your response MUST follow this EXACT format:
Frame [timestamp]: [1-2 concise sentences about what's new]

For example:
Frame 2.50: A person demonstrates the product with an excited expression. Text overlay shows "AMAZING RESULTS".

DO NOT deviate from this format. Each frame description MUST start with "Frame" followed by the timestamp.
```

## Native Video Analysis

### Template: native_video_timeline
```
Analyze this marketing video and list each distinct scene with timestamp and description.

Focus on:
- Visual content and key moments
- Transitions and flow between scenes
- Camera movements and pacing
- Text overlays and graphics

Format each line as: timestamp: description

Example:
0.0: Woman speaks to camera with warning sign backdrop
3.5: Smooth transition to product demo, camera zooms to tablet
6.0: Close-up hands interacting with colorful game pieces
10.0: Text overlay "Download Now" appears with CTA button

Be specific about visuals, transitions, and timing.
```
