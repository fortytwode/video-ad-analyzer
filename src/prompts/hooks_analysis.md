# Hooks Analysis

## Spoken Hooks

### Template: hooks_spoken
```
Analyze ONLY the spoken dialogue in the first few seconds:

Transcript: {{transcript}}

A "spoken hook" is what is SAID (not shown) in the opening moments that captures attention. This could be a question, bold statement, relatable problem, surprising fact, or emotional appeal delivered through words/voice.

Do NOT analyze visual elements, text overlays, or music. Focus exclusively on the spoken content.

Your analysis must identify:
1. **Pattern Category**: Classify the hook strategy (e.g., "Authority/Expert", "Bold Claim/Promise", "Provocative Question", "Problem Statement", "Curiosity Gap", "Social Proof")
2. **Evidence**: Quote the exact spoken words that act as the hook (within first 5-10 seconds of audio)
3. **Marketing Impact**: Explain why this hook pattern is effective for this audience

Only analyze the first hook—the spoken words that occur within the first 5-10 seconds. Exclude any hooks that appear later in the video.

IMPORTANT: The "pattern_name" field must contain the HOOK STRATEGY CATEGORY (like "Authority/Expert" or "Bold Claim"), NOT the literal hook text.

Format as exact JSON:
{
    "elements": [
        {
            "pattern_name": "<hook strategy category>",
            "evidence": "<exact spoken words>",
            "marketing_impact": "<why this pattern works>"
        }
    ],
    "context": "<video/creative identifier>"
}
```

## Visual Hooks

### Template: hooks_visual
```
Analyze the opening visual elements:

Early visuals: {{early_frames}}

A "visual hook" is any visual element that immediately captures attention within the first few seconds. This can include people, characters, striking imagery, unusual scenes, emotional expressions, or visual demonstrations of problems/solutions. Do NOT include text overlays or spoken dialogue as part of the visual hook—they are analyzed separately.

Your analysis must identify:
1. **Pattern Category**: Classify the visual hook strategy (e.g., "Authority Figure", "Talking Head/Expert", "Text-Heavy List", "Split Screen Comparison", "Problem Demonstration", "Striking Imagery")
2. **Evidence**: Describe the specific visual elements that act as hooks (imagery, actions, scenes, persons, emotional expressions). Do NOT include text overlays or spoken dialogue.
3. **Marketing Impact**: Explain why this visual pattern is effective for capturing attention

Only analyze the first hook—the visual elements that occur within the first 5 seconds. Exclude any hooks that appear after the first 5 seconds.

IMPORTANT: The "pattern_name" field must contain the VISUAL HOOK STRATEGY CATEGORY (like "Authority Figure" or "Talking Head"), NOT a description of the exact visuals.

Format as exact JSON:
{
    "elements": [
        {
            "pattern_name": "<visual hook strategy category>",
            "evidence": "<description of visual elements>",
            "marketing_impact": "<why this visual pattern works>"
        }
    ],
    "context": "<video/creative identifier>"
}
```

## Text Overlay Hooks

### Template: hooks_text
```
Analyze how text overlays are used as hooks in this content:

Text overlays: {{text_timeline}}
Scenes: {{scenes}}

A "text hook" is any on-screen text (titles, captions, subtitles, graphics) that appears early and captures attention. This could include bold statements, questions, numbers, or promises displayed as text.

Do NOT analyze spoken words or purely visual elements. Focus on text that appears on screen.

Your analysis must identify:
1. **Pattern Category**: Classify the text hook strategy (e.g., "Authority/Secret", "Bold Claim/Promise", "Provocative Question", "Number/Statistic", "Problem Statement", "How-To/Framework", "Historical/Mogul Reference")
2. **Evidence**: Quote the exact text overlay that acts as the hook (within first 5 seconds)
3. **Marketing Impact**: Explain why this text pattern is effective for capturing attention

Only analyze the first hook—text overlays that appear within the first 5 seconds. Exclude any text that appears later in the video.

IMPORTANT: The "pattern_name" field must contain the TEXT HOOK STRATEGY CATEGORY (like "Authority/Secret" or "Bold Claim"), NOT the literal text content.

Format as exact JSON:
{
    "elements": [
        {
            "pattern_name": "<text hook strategy category>",
            "evidence": "<exact text overlay>",
            "marketing_impact": "<why this text pattern works>"
        }
    ],
    "context": "<video/creative identifier>"
}
```
