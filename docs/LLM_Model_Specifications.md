# Agent9 LLM Hackathon Model Specifications

This document outlines the specific LLM models and configuration settings to be used for the Agent9 LLM Hackathon. Following these specifications ensures experimental consistency and fair comparison between different models.

## Model Selection

The following models available in Cascade have been selected for the hackathon:

| Provider | Model | Description |
|----------|-------|-------------|
| OpenAI   | GPT-4 | Advanced reasoning model with strong coding capabilities |
| Google   | Gemini Pro | Google's advanced model with reasoning and coding abilities |
| Anthropic | Claude | Anthropic's model with strong reasoning and instruction following |

## Temperature Settings by Phase

Each phase of the hackathon requires different levels of creativity versus precision:

### Phase 1: Requirements Clarification

During the requirements clarification phase, we prioritize precision, analytical thinking, and gap identification over creativity.

| Model | Temperature | Additional Parameters |
|-------|-------------|----------------------|
| GPT-4 | 0.3 | top_p=0.95 |
| Gemini Pro | 0.4 | top_k=40 |
| Claude | 0.5 | top_p=0.9 |

### Phase 2: Implementation

During the implementation phase, we allow for more creativity in solution design while maintaining enough focus to produce functional code.

| Model | Temperature | Additional Parameters |
|-------|-------------|----------------------|
| GPT-4 | 0.7 | top_p=0.95 |
| Gemini Pro | 0.8 | top_k=40 |
| Claude | 0.7 | top_p=0.9 |

## Consistency Requirements

To ensure experimental validity:

1. **Same Model Version**: Use the same model version for both Phase 1 and Phase 2 for each provider
2. **Documented Settings**: Record the exact model version and parameter settings used in each session
3. **Isolated Sessions**: Do not share insights between models during the experiment
4. **Credit Tracking**: Track the number of tokens/credits consumed by each model

## Session Configuration Instructions

### OpenAI (GPT-4)

```
Model: gpt-4
Phase 1:
  temperature: 0.3
  top_p: 0.95
  max_tokens: 8000
Phase 2:
  temperature: 0.7
  top_p: 0.95
  max_tokens: 8000
```

### Google (Gemini Pro)

```
Model: gemini-pro
Phase 1:
  temperature: 0.4
  top_k: 40
  max_output_tokens: 8000
Phase 2:
  temperature: 0.8
  top_k: 40
  max_output_tokens: 8000
```

### Anthropic (Claude)

```
Model: claude
Phase 1:
  temperature: 0.5
  top_p: 0.9
  max_tokens_to_sample: 8000
Phase 2:
  temperature: 0.7
  top_p: 0.9
  max_tokens_to_sample: 8000
```

## Prompt Engineering Guidelines

For consistent results across models:

1. **Clear Instructions**: Provide clear, explicit instructions at the beginning of each prompt
2. **Context Inclusion**: Include relevant context from PRDs and design documents
3. **Structured Format**: Use consistent formatting and structure across all models
4. **Step-by-Step Guidance**: Break complex tasks into smaller steps
5. **Explicit Expectations**: Clearly state the expected output format

## Evaluation Metrics

The following metrics will be tracked for each model:

1. **Relevance**: How well the solution addresses the requirements (1-10)
2. **Accuracy**: Correctness of implementation (1-10)
3. **Bugginess**: Number of bugs or issues identified (lower is better)
4. **Speed**: Time to complete implementation (lower is better)
5. **Cost**: Number of tokens/credits consumed (lower is better)

## Documentation Requirements

For each session, document:

1. Exact model version used
2. All parameter settings
3. Session duration
4. Token/credit consumption
5. Any deviations from the standard configuration

This information should be included in the session outcome documents in the `docs/clarification_sessions/` directory.
