# Marketing Analysis Prompts (v2 - Framework Update)

## 💔 Problem Analysis

### Template: problem
```
Analyze how this ad frames tension, pain, or loss aversion.

Transcript: {{transcript}}
Text overlays: {{text_timeline}}
Scenes: {{scenes}}

IMPORTANT: Base your analysis ONLY on the actual ad content provided above. Do NOT create hypothetical scenarios.

Consider:
- Explicit frustrations, inconveniences, or fears mentioned
- Implicit loss aversion ("you're missing out", "leaving money on the table")
- Missed opportunities or inefficiencies highlighted
- Social discomfort or status anxiety
- Time waste, complexity, or effort mentioned
- Risk or uncertainty framed

Identify the SINGLE MOST IMPORTANT problem pattern in the ad if available.
Focus on the problem that has the strongest marketing impact and drives the most tension.

Rate the SALIENCE of this problem framing based on its MARKETING IMPACT:

Salience measures: How much does this problem framing drive conversions and persuade the audience to act?

- 0.9-1.0: CRITICAL to conversion - Core pain point that directly drives purchase intent (e.g., specific costly problem with immediate urgency, acute pain that demands solution)
- 0.7-0.8: STRONG impact - Clear problem that motivates action (e.g., relatable frustration that creates desire for solution)
- 0.5-0.6: MODERATE impact - Present but doesn't strongly drive conversion (e.g., generic problem, weak emotional pull)
- 0.0-0.4: LOW/NO impact - Weak problem framing that doesn't persuade (e.g., vague or irrelevant pain point)

Consider these factors when rating marketing impact:
1. Conversion potential - Does this problem make someone want to buy NOW?
2. Emotional intensity - How painful/urgent does it feel to the target audience?
3. Relatability - Would the audience immediately recognize and feel this pain?
4. Specificity - Is it concrete enough to drive action?

CRITICAL: If salience score is BELOW 0.5, return empty elements:
{
  "elements": [],
  "context": "Problem dimension not salient enough (score < 0.5) - insufficient marketing impact",
  "salience_score": [actual score]
}

Do NOT force-fit weak signals. Better to return empty than fabricate weak patterns.

Provide:
1. A descriptive name for the problem pattern
2. Exact evidence from the ad (quote or scene description)
3. The marketing impact of framing this problem
4. Salience score (0.0 to 1.0)

Format as exact JSON:
{
    "elements": [{
        "pattern_name": "",
        "evidence": "",
        "marketing_impact": ""
    }],
    "context": "",
    "salience_score": 0.0
}
```

## 🌅 Aspiration & Transformation Analysis

### Template: aspiration_transformation
```
Analyze the desired future state, transformation, or aspirational outcome shown or implied in this ad.

Transcript: {{transcript}}
Text overlays: {{text_timeline}}
Scenes: {{scenes}}

IMPORTANT: Base your analysis ONLY on the actual ad content provided above. Do NOT create hypothetical scenarios.

Consider:
- Before/After contrasts (visual or spoken)
- Emotional payoff (relief, empowerment, joy, pride)
- Status or identity upgrade ("become the person who...")
- Capability gains ("now you can...")
- Time/freedom/resource abundance
- Transformation moments or milestone achievements

Identify the SINGLE MOST IMPORTANT aspirational or transformation pattern in the ad if available.
Focus on the outcome that has the strongest marketing impact and emotional pull.

Rate the SALIENCE of this aspiration/transformation based on its MARKETING IMPACT:

Salience measures: How much does this aspirational messaging drive conversions and persuade the audience to act?

- 0.9-1.0: CRITICAL to conversion - Core promise that directly drives purchase intent (e.g., dramatic transformation with clear "after" state, highly desirable outcome that compels action)
- 0.7-0.8: STRONG impact - Clear aspiration that motivates purchase (e.g., specific relatable outcome, emotional payoff that creates desire)
- 0.5-0.6: MODERATE impact - Present but doesn't strongly drive conversion (e.g., generic benefit, vague future state with weak pull)
- 0.0-0.4: LOW/NO impact - Weak aspirational messaging that doesn't persuade (e.g., unclear transformation, uncompelling outcome)

Consider these factors when rating marketing impact:
1. Conversion potential - Does this aspiration make someone want to buy NOW?
2. Emotional pull - How compelling and desirable is this "after" state?
3. Clarity & vividness - Can the audience clearly visualize and feel the transformation?
4. Differentiation - Is this outcome unique/special enough to drive action?

CRITICAL: If salience score is BELOW 0.5, return empty elements:
{
  "elements": [],
  "context": "Aspiration/transformation dimension not salient enough (score < 0.5) - insufficient marketing impact",
  "salience_score": [actual score]
}

Do NOT force-fit weak signals. Better to return empty than fabricate weak patterns.

Provide:
1. A descriptive name for the aspiration/transformation pattern
2. Exact evidence from the ad (quote or scene description showing the desired outcome)
3. The marketing impact of this aspirational messaging
4. Salience score (0.0 to 1.0)

Format as exact JSON:
{
    "elements": [{
        "pattern_name": "",
        "evidence": "",
        "marketing_impact": ""
    }],
    "context": "",
    "salience_score": 0.0
}
```

## 🤝 Credibility Analysis

### Template: credibility
```
Analyze how this ad builds trust, credibility, and reduces perceived risk.

Transcript: {{transcript}}
Text overlays: {{text_timeline}}
Scenes: {{scenes}}

IMPORTANT: Base your analysis ONLY on the actual ad content provided above. Do NOT create hypothetical scenarios.

Consider:
- Testimonials or user reviews (social proof)
- Expert endorsements or authority figures
- Data, statistics, or research citations
- Before/after evidence or case studies
- Risk reversal (guarantees, free trials, money-back promises)
- Specificity and transparency (exact numbers, real names, verifiable claims)
- Brand trust signals (certifications, awards, partnerships)
- Objection handling (addressing common concerns or skepticism)

Identify the SINGLE MOST IMPORTANT credibility element in the ad if available.
Focus on the proof mechanism that has the strongest marketing impact in building trust.

Rate the SALIENCE of this credibility element based on its MARKETING IMPACT:

Salience measures: How much does this credibility mechanism drive conversions by building trust and reducing purchase risk?

- 0.9-1.0: CRITICAL to conversion - Powerful proof that directly overcomes skepticism and drives purchase (e.g., compelling testimonial with specific results, authoritative data that eliminates doubt)
- 0.7-0.8: STRONG impact - Clear credibility signal that builds trust (e.g., specific social proof, expert endorsement, concrete evidence)
- 0.5-0.6: MODERATE impact - Present but doesn't strongly reduce risk (e.g., generic testimonial, vague claims, weak proof)
- 0.0-0.4: LOW/NO impact - Weak credibility signals that don't persuade (e.g., unverifiable claims, no proof provided)

Consider these factors when rating marketing impact:
1. Conversion potential - Does this proof make someone trust enough to buy NOW?
2. Specificity - Are claims concrete and verifiable vs vague?
3. Source credibility - How authoritative/relatable is the proof source?
4. Risk reduction - Does it address and overcome skepticism?

CRITICAL: If salience score is BELOW 0.5, return empty elements:
{
  "elements": [],
  "context": "Credibility dimension not salient enough (score < 0.5) - insufficient marketing impact",
  "salience_score": [actual score]
}

Do NOT force-fit weak signals. Better to return empty than fabricate weak patterns.

Provide:
1. A descriptive name for the credibility pattern
2. Exact evidence from the ad (quote or scene description)
3. The marketing impact of this credibility element
4. Salience score (0.0 to 1.0)

Format as exact JSON:
{
    "elements": [{
        "pattern_name": "",
        "evidence": "",
        "marketing_impact": ""
    }],
    "context": "",
    "salience_score": 0.0
}
```

## ⏰ Urgency Analysis

### Template: urgency
```
Analyze elements that create urgency, scarcity, or temporal pressure to act now.

Transcript: {{transcript}}
Text overlays: {{text_timeline}}
Scenes: {{scenes}}

IMPORTANT: Base your analysis ONLY on the actual ad content provided above. Do NOT create hypothetical scenarios.

Consider:
- Time-limited offers (deadlines, countdowns, "today only")
- Scarcity signals (limited quantity, selling out, high demand)
- Trending/momentum indicators ("50K joined", "going viral")
- Temporal loss aversion ("don't miss out", "last chance")
- Exclusive access windows (early access, beta, limited slots)
- Competition pressure (others are acting, spots filling up)

Identify the SINGLE MOST IMPORTANT urgency element in the ad if available.
Focus on the urgency mechanism that has the strongest marketing impact in prompting immediate action.

Rate the SALIENCE of this urgency element based on its MARKETING IMPACT:

Salience measures: How much does this urgency mechanism drive conversions by creating pressure to act NOW vs later?

- 0.9-1.0: CRITICAL to conversion - Powerful urgency that directly drives immediate action (e.g., specific deadline with clear consequence, compelling scarcity with proof)
- 0.7-0.8: STRONG impact - Clear urgency signal that motivates faster action (e.g., time-limited offer, trending momentum, visible scarcity)
- 0.5-0.6: MODERATE impact - Present but doesn't strongly drive immediate action (e.g., generic "act now", weak scarcity claim)
- 0.0-0.4: LOW/NO impact - Weak or no urgency signals (e.g., no temporal pressure, evergreen offer)

Consider these factors when rating marketing impact:
1. Conversion potential - Does this make someone act NOW instead of "maybe later"?
2. Specificity - Is the urgency concrete (specific deadline/quantity) vs vague?
3. Credibility - Is the scarcity/urgency believable and verifiable?
4. Consequence clarity - Is it clear what happens if they wait?

CRITICAL: If salience score is BELOW 0.5, return empty elements:
{
  "elements": [],
  "context": "Urgency dimension not salient enough (score < 0.5) - insufficient marketing impact",
  "salience_score": [actual score]
}

Do NOT force-fit weak signals. Better to return empty than fabricate weak patterns.

Provide:
1. A descriptive name for the urgency pattern
2. Exact evidence from the ad (quote or scene description)
3. The marketing impact of this urgency element
4. Salience score (0.0 to 1.0)

Format as exact JSON:
{
    "elements": [{
        "pattern_name": "",
        "evidence": "",
        "marketing_impact": ""
    }],
    "context": "",
    "salience_score": 0.0
}
```

## 🎬 Visual Format Analysis

### Template: visual_format
```
Analyze the visual production style and format of this ad.

Transcript: {{transcript}}
Text overlays: {{text_timeline}}
Scenes: {{scenes}}

IMPORTANT: Base your analysis ONLY on the actual ad content provided above. Do NOT create hypothetical scenarios.

Consider:
- UGC-style (user-generated content: talking head, casual, authentic, smartphone-shot)
- Professional production (studio lighting, actors, cinematic, high polish)
- Animation/motion graphics (animated characters, kinetic typography, illustrated)
- Screen recording (app demo, website walkthrough, tutorial-style)
- Text-heavy/voiceless (primarily text overlays, minimal or no spoken content)
- Mixed media (combination of multiple formats)
- Spokesperson/host (on-camera presenter, direct-to-camera)

Identify the PRIMARY visual format that defines this ad's production style.

Rate the SALIENCE of this visual format based on its MARKETING IMPACT:

Salience measures: How much does this visual format contribute to conversions through authenticity, attention, or message delivery?

- 0.9-1.0: CRITICAL to conversion - Format is essential to the message and drives trust/attention (e.g., authentic UGC that builds credibility, screen recording that proves product works)
- 0.7-0.8: STRONG impact - Format meaningfully enhances persuasion (e.g., professional production signals quality, animation clarifies complex concept)
- 0.5-0.6: MODERATE impact - Format is present but not distinctive or essential (e.g., generic talking head, standard product shots)
- 0.0-0.4: LOW/NO impact - Format doesn't contribute meaningfully to conversion

Consider these factors when rating marketing impact:
1. Conversion potential - Does this format build trust or drive action?
2. Distinctiveness - Is the format unique or memorable vs generic?
3. Message fit - Does format enhance the core message delivery?
4. Production quality - Is execution aligned with brand positioning?

CRITICAL: If salience score is BELOW 0.5, return empty elements:
{
  "elements": [],
  "context": "Visual format not distinctive enough (score < 0.5) - insufficient marketing impact",
  "salience_score": [actual score]
}

Provide:
1. A descriptive name for the visual format
2. Exact evidence from scenes/visuals
3. The marketing impact of this format choice
4. Salience score (0.0 to 1.0)

Format as exact JSON:
{
    "elements": [{
        "pattern_name": "",
        "evidence": "",
        "marketing_impact": ""
    }],
    "context": "",
    "salience_score": 0.0
}
```

## ⏩ Narrative Flow Analysis

### Template: narrative_flow
```
Describe the persuasion sequence and story structure of this ad.

Transcript: {{transcript}}
Text overlays: {{text_timeline}}
Scenes: {{scenes}}

IMPORTANT: Base your analysis ONLY on the actual ad content provided above.

Identify the narrative archetype and beat sequence:

Archetypes:
- Story (character arc, narrative journey)
- Listicle (numbered tips, multiple points)
- Demo (product demonstration, how-it-works)
- Testimonial-led (user experience drives structure)
- Problem-Solution (pain point → product fix)
- Offer-first (lead with deal/promotion)

Beat Order: Sequence of persuasion clusters (attention → problem → aspiration → credibility → urgency)

CTA Timing: Approximate second when call-to-action or payoff appears

Rate the SALIENCE of this narrative flow based on its MARKETING IMPACT:

Salience measures: How much does the story structure contribute to conversions through engagement and message sequencing?

- 0.9-1.0: CRITICAL - Narrative structure is core to persuasion (e.g., compelling story arc that drives emotional journey, perfect beat sequence)
- 0.7-0.8: STRONG - Clear structure enhances message delivery (e.g., logical problem-solution flow, effective demonstration sequence)
- 0.5-0.6: MODERATE - Structure present but not distinctive (e.g., generic sequence, weak story)
- 0.0-0.4: LOW/NO - No clear narrative structure or doesn't impact conversion

CRITICAL: If salience score is BELOW 0.5, return empty elements:
{
  "elements": [],
  "context": "Narrative flow not salient enough (score < 0.5) - insufficient marketing impact",
  "salience_score": [actual score]
}

Do NOT force-fit weak signals. Better to return empty than fabricate weak patterns.

Provide:
1. A descriptive name combining archetype and structure (pattern_name)
2. Exact evidence including archetype, beat order, and CTA timing (evidence)
3. The marketing impact of this narrative structure (marketing_impact)
4. Salience score (0.0 to 1.0)

Format as exact JSON:
{
    "elements": [{
        "pattern_name": "",
        "evidence": "Archetype: [name], Beat order: [list], CTA timing: [X]s",
        "marketing_impact": ""
    }],
    "context": "",
    "salience_score": 0.0
}
```

## 🎭 Emotion Analysis

### Template: emotion
```
Analyze the emotional tone and energy of this ad.

Transcript: {{transcript}}
Text overlays: {{text_timeline}}
Scenes: {{scenes}}

IMPORTANT: Base your analysis ONLY on the actual ad content provided above.

Identify the emotional characteristics:

Valence: Emotional positivity/negativity (-1.0 to +1.0)
- Negative (-1.0 to -0.3): Fear, anxiety, frustration, sadness
- Neutral (-0.3 to +0.3): Informational, matter-of-fact
- Positive (+0.3 to +1.0): Hope, excitement, joy, pride

Arousal: Energy level (low/medium/high)
- Low: Calm, relaxed, peaceful
- Medium: Engaged, interested, motivated
- High: Excited, urgent, intense

Dominant Emotion: Primary emotional driver (e.g., "relief", "excitement", "anxiety", "sadness", "hope", "pride", "curiosity", "urgency", "trust" - THIS IS NOT AN EXHAUSTIVE LIST)

Rate the SALIENCE of this emotional tone based on its MARKETING IMPACT:

Salience measures: How much does the emotional tone drive conversions through emotional engagement and resonance?

- 0.9-1.0: CRITICAL - Emotion is core to persuasion (e.g., powerful emotional journey, perfectly calibrated tone for target audience)
- 0.7-0.8: STRONG - Clear emotional driver that enhances persuasion (e.g., relatable feeling, effective emotional arc)
- 0.5-0.6: MODERATE - Emotion present but not distinctive (e.g., generic positive tone, weak emotional pull)
- 0.0-0.4: LOW/NO - Weak or absent emotional tone that doesn't drive conversion

CRITICAL: If salience score is BELOW 0.5, return empty elements:
{
  "elements": [],
  "context": "Emotion dimension not salient enough (score < 0.5) - insufficient marketing impact",
  "salience_score": [actual score]
}

Do NOT force-fit weak signals. Better to return empty than fabricate weak patterns.

Consider these factors:
1. Emotional clarity - Is the feeling distinct and intentional?
2. Target alignment - Does this emotion resonate with target audience's state/needs?
3. Conversion alignment - Does this emotion drive desired action?

Provide:
1. A descriptive name for the emotional tone (pattern_name)
2. Exact evidence including valence score, arousal level, and dominant emotion (evidence)
3. The marketing impact of this emotional approach (marketing_impact)
4. Salience score (0.0 to 1.0)

Format as exact JSON:
{
    "elements": [{
        "pattern_name": "",
        "evidence": "Valence: [score], Arousal: [level], Dominant emotion: [name]",
        "marketing_impact": ""
    }],
    "context": "",
    "salience_score": 0.0
}
```

## 👥 Target Audience Analysis

### Template: target_audience
```
Identify the primary target audience for this ad based on contextual clues.

Transcript: {{transcript}}
Text overlays: {{text_timeline}}
Scenes: {{scenes}}

IMPORTANT: Base your analysis ONLY on the actual ad content provided above. Do NOT create hypothetical scenarios.

Infer target audience from:
- **Problem language** - What pain points are emphasized? (e.g., "busy moms", "entrepreneurs", "fitness enthusiasts")
- **Aspiration framing** - What outcomes are promised? (e.g., family time vs career success vs physical transformation)
- **Visual styling** - Who appears in the ad? What settings? What lifestyle signals?
- **Messaging tone** - Casual vs professional? Technical vs emotional? Aspirational vs practical?
- **Product context** - Who typically uses this type of product/service?
- **Demographic signals** - Age, gender, life stage, occupation, income level (if evident)

Identify the SINGLE PRIMARY audience segment (or 2-3 if clearly multi-targeted).

Rate the CONFIDENCE of this audience inference:

Confidence measures: How clear and specific is the targeting in this ad?

- 0.9-1.0: VERY CLEAR - Explicit targeting (e.g., "For busy working moms", specific demographic in visuals, highly specific problem/aspiration)
- 0.7-0.8: CLEAR - Strong contextual clues (e.g., consistent lifestyle signals, specific problem domain, targeted messaging tone)
- 0.5-0.6: MODERATE - Some clues but could appeal to multiple segments (e.g., generic language, broad appeal visuals)
- 0.0-0.4: UNCLEAR - Vague or very broad targeting (e.g., "everyone" appeal, no specific signals)

CRITICAL: If confidence score is BELOW 0.5, still provide best inference but note low confidence:
{
  "elements": [{
    "pattern_name": "[Best inference]",
    "evidence": "Weak signals: [what you observed]",
    "marketing_impact": "Broad/unclear targeting limits message resonance"
  }],
  "context": "Target audience inference has low confidence (score < 0.5) - targeting is vague or very broad",
  "salience_score": [actual score]
}

Provide:
1. A descriptive name for the target audience segment (pattern_name)
2. Exact evidence from the ad showing why you inferred this audience (evidence)
3. The marketing impact of this targeting approach (marketing_impact)
4. Confidence/salience score (0.0 to 1.0)

Format as exact JSON:
{
    "elements": [{
        "pattern_name": "",
        "evidence": "",
        "marketing_impact": ""
    }],
    "context": "",
    "salience_score": 0.0
}
```
