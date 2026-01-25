# Pattern Normalization - Strategic Analysis

## Context
You are analyzing the **{{dimension_name}}** dimension from **{{total_videos}}** marketing videos.

Each video has already been analyzed to extract the MOST SALIENT pattern for this dimension (via AI-powered salience scoring in a previous step). Your job is to group these patterns into strategic categories.

## Input Data
Below is a JSON array of all patterns found, one per video:

```json
{{patterns_json}}
```

Each object contains:
- `index`: The video's position in the array (used for grouping)
- `description`: The extracted pattern description

## Task
Group these patterns into **3-7 normalized categories** that represent DISTINCT strategic approaches or marketing angles.

## Grouping Principles
1. **Strategic Intent Over Words:** Group by underlying marketing strategy, not just similar wording
   - Example: "Fear of missing out" and "Left behind by peers" = same strategy
   
2. **Concise Labels:** Create category names that are strategic and concise
   - ✅ Good: "FOMO / Missed Opportunity"
   - ✅ Good: "Authority Figure / Expert"
   - ❌ Bad: "people who are missing out on things"
   - ❌ Bad: "description about experts"

3. **Complete Coverage:** Every pattern must be assigned to exactly ONE category

4. **Balance:** Aim for 3-7 categories (not too few, not too many)

## Output Format
Return ONLY valid JSON in this exact structure:

```json
{
  "Authority Figure / Expert": [0, 3, 7, 12, 15],
  "Historical Success / Mogul": [1, 5, 9, 14],
  "Provocative Question": [2, 4, 6, 8, 10, 11, 13]
}
```

**Keys:** Strategic category labels (concise, strategic)
**Values:** Arrays of pattern indices that belong to this category

## Critical Requirements
- Output ONLY the JSON object
- No explanations, no markdown formatting, no preamble
- All indices must be valid (0 to {{total_videos}}-1)
- Every index from input must appear exactly once in output
