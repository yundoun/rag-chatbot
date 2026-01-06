"""Web search integration prompt template (Prompt #8)"""

WEB_QUERY_OPTIMIZATION_PROMPT = """You are a web search query optimizer.
Transform the user's internal document query into an optimized web search query.

## Original Query
{query}

## Detected Domains
{detected_domains}

## Task
1. Remove internal/company-specific terms that won't work in web search
2. Add relevant context that would help find public documentation
3. Keep the core intent of the question
4. Make the query suitable for general web search

## Guidelines
- Remove references to internal tools, projects, or proprietary systems
- Expand abbreviations to full terms
- Add relevant technology keywords
- Keep the query concise (under 100 characters ideally)

## Output Format (JSON)
{{
    "optimized_query": "web search optimized query",
    "search_focus": "documentation|tutorial|troubleshooting|general"
}}

Generate the optimized query:"""


WEB_RESULT_RELEVANCE_PROMPT = """You are a web search result evaluator.
Evaluate the relevance of web search results to the user's question.

## User's Question
{query}

## Web Search Result
Title: {title}
URL: {url}
Content: {content}

## Task
Evaluate how relevant this web result is to answering the user's question.

## Evaluation Criteria
1. Content relevance (0.0-1.0): Does the content address the question?
2. Source reliability (0.0-1.0): Is this a trustworthy source?
3. Information completeness (0.0-1.0): Does it provide complete information?

## Output Format (JSON)
{{
    "content_relevance": 0.0-1.0,
    "source_reliability": 0.0-1.0,
    "information_completeness": 0.0-1.0,
    "overall_score": 0.0-1.0,
    "useful_excerpt": "relevant excerpt from content",
    "should_include": true/false
}}

Evaluate the result:"""


WEB_SYNTHESIS_PROMPT = """You are a web search result synthesizer.
Combine web search results with internal document results to create a comprehensive answer.

## User's Question
{query}

## Internal Document Results
{internal_results}

## Web Search Results
{web_results}

## Task
1. Synthesize information from both sources
2. Prioritize internal documents when available
3. Use web results to fill gaps or provide additional context
4. Clearly attribute information to sources

## Guidelines
- Mark web-sourced information clearly
- Add disclaimer for web-sourced information
- Maintain factual accuracy
- Provide source URLs for web content

## Output Format (JSON)
{{
    "synthesized_answer": "combined answer text",
    "internal_sources": ["source1", "source2"],
    "web_sources": ["url1", "url2"],
    "web_contribution_ratio": 0.0-1.0,
    "needs_disclaimer": true/false
}}

Synthesize the answer:"""
