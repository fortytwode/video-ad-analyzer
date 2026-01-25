# Strategic Formula Generation

## Context
You are generating a strategic formula that captures the marketing mechanism for a pattern category.

**Dimension:** {{dimension_name}}  
**Pattern Category:** {{pattern_label}}  
**Frequency:** {{frequency}}% of {{total_videos}} videos use this pattern

## Examples from This Category
```json
{{examples_json}}
```

## Task
Generate a concise **schematic formula** that captures the strategic structure and mechanism of this pattern.

## Formula Style Guide

### Operators
- `→` for transformation, causation, or flow
- `+` for combination or addition
- `=` for resulting outcome
- `[ ]` for strategic elements

### Formula Components
Each element in brackets should represent a strategic concept, not literal content:

✅ **Good Elements:**
- `[Expert Authority]`
- `[Quantified Secret]` 
- `[Personal Flaw]`
- `[Structured Learning]`
- `[Emotional Transformation]`

❌ **Bad Elements:**
- `[The expert says]` (too literal)
- `[something secret]` (too vague)
- `[you have a problem]` (not strategic)

### Example Formulas

**Pattern: Authority Hook**
- `[Expert Authority] + [Quantified Secret] → [Immediate Intrigue]`

**Pattern: FOMO / Missed Opportunity**  
- `[Current Status] → [Elite Secret] = [Underachievement Feeling]`

**Pattern: Transformation Promise**
- `[Personal Flaw] + [Structured Learning] → [Emotional Transformation]`

**Pattern: Social Proof**
- `[Prestigious Source] + [Endorsement] = [Trust & Credibility]`

## Requirements
1. **Concise:** 3-5 elements maximum
2. **Strategic:** Capture the marketing mechanism, not just the content
3. **Generalizable:** Should apply to all examples in this category
4. **Clear Structure:** Use operators logically (input → process = outcome)

## Output Format
Return ONLY the formula string. 

No explanations, no quotes, no markdown, no preamble.

Just the formula.

Example output:
[Expert Knowledge] + [Application Method] = [Life Transformation]
