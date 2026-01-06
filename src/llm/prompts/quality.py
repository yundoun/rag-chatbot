"""Response Quality Evaluation Prompt Template (Prompt #7)"""

QUALITY_EVALUATION_PROMPT = """Evaluate the quality of the generated response.

## User Query
{query}

## Generated Response
{response}

## Sources Used
{sources}

## Evaluation Criteria

1. **completeness** (0.0 - 1.0): Does the response fully answer the query?
   - 1.0: Completely answers all aspects of the query
   - 0.8: Answers main aspects, minor details missing
   - 0.6: Partially answers, significant gaps
   - 0.4: Addresses topic but doesn't answer query
   - 0.2: Barely related to query
   - 0.0: Does not address query at all

2. **accuracy** (0.0 - 1.0): Is the information accurate based on sources?
   - 1.0: All information directly supported by sources
   - 0.8: Most information supported, minor inferences
   - 0.6: Some unsupported claims but mostly accurate
   - 0.4: Mixed accuracy, some contradictions
   - 0.2: Mostly unsupported or inaccurate
   - 0.0: Contradicts sources or fabricated

3. **clarity** (0.0 - 1.0): Is the response clear and well-structured?
   - 1.0: Crystal clear, well-organized, easy to follow
   - 0.8: Clear with good structure
   - 0.6: Understandable but could be clearer
   - 0.4: Somewhat confusing or poorly organized
   - 0.2: Difficult to understand
   - 0.0: Incomprehensible

4. **confidence**: Overall confidence score (weighted average)
   - Formula: (completeness * 0.4) + (accuracy * 0.4) + (clarity * 0.2)

5. **needs_disclaimer**: Should a disclaimer be shown?
   - true: if confidence < 0.8 OR completeness < 0.6 OR accuracy < 0.7
   - false: otherwise

## Response Format
Return a JSON object with:
- completeness: float
- accuracy: float
- clarity: float
- confidence: float
- needs_disclaimer: boolean
"""
