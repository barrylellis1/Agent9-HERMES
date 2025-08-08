# Agent9-HERMES Prompt Templates

## sql_generation
Template for SQL generation from natural language queries.

```template
Generate a SQL query that answers the following question:

Question: {{natural_language_query}}

Context:
- The query should be executed against {{data_product_id}}
- Focus on clarity and performance
- Use only standard SQL syntax compatible with DuckDB

{{#if yaml_contract}}
Data Product Contract:
```yaml
{{yaml_contract}}
```
{{/if}}

Your response should be structured as JSON:
{
  "sql_query": "<SQL query>",
  "confidence": <0.0-1.0>,
  "explanation": "<explanation of approach>",
  "warnings": ["<any potential issues>"]
}
```

## summarization
Template for summarizing content.

```template
Summarize the following information concisely and accurately:

{{content}}

{{#if max_length}}
Keep the summary under {{max_length}} words.
{{/if}}

{{#if focus_areas}}
Focus particularly on: {{focus_areas}}
{{/if}}
```

## analysis
Template for analyzing content.

```template
Analyze the following content:

{{content}}

Analysis type: {{analysis_type}}

{{#if context}}
Additional context:
{{context}}
{{/if}}

Provide a structured analysis in JSON format with relevant insights.
```

## evaluation
Template for evaluating options against criteria.

```template
Evaluate the following options based on the provided criteria:

Options:
{{#each options}}
- {{this}}
{{/each}}

Criteria:
{{#each criteria}}
- {{this}}
{{/each}}

{{#if context}}
Context:
{{context}}
{{/if}}

Rank the options and provide a rationale for each ranking.
Return your evaluation in JSON format with rankings, scores (1-10), and rationale.
```

## decision
Template for making decisions with trade-off analysis.

```template
Make a decision on the following question:

Question: {{question}}

Options:
{{#each options}}
- {{this}}
{{/each}}

Considerations:
{{#each considerations}}
- {{this}}
{{/each}}

Analyze the trade-offs of each option and recommend the best approach.
Provide your reasoning and any relevant caveats.
```

## data_exploration
Template for exploring data characteristics.

```template
Explore the following dataset and identify key patterns:

{{dataset_description}}

Tables:
{{#each tables}}
- {{this.name}}: {{this.description}}
{{/each}}

Identify:
1. Key relationships between entities
2. Potential insights or trends
3. Data quality concerns
4. Recommendations for analysis

Keep the response focused on business-relevant insights.
```
