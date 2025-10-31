# Running Live LLM Validation Checks

Live LLM checks complement the stubbed unit tests by exercising the Data Product Agent end-to-end with a real language model. They remain opt-in so the main CI stays fast and offline-friendly.

## Prerequisites

1. Valid API credentials exported in your shell (for example, `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` depending on the configured provider).
2. `A9_RUN_LLM_LIVE=1` set in the environment to explicitly opt in to live tests.
3. Network access from your development environment to the model endpoint.

## Running the tests

```bash
A9_RUN_LLM_LIVE=1 OPENAI_API_KEY=... pytest -m llm_live
```

The marker `llm_live` isolates the handful of integration tests that talk to real services. If the required environment variables are missing, the tests are skipped with a clear message.

## What the tests cover

- `A9_Data_Product_Agent.generate_sql` delegated through the orchestrator to the live LLM service.
- Basic invariants on the returned SQL (non-empty, syntactically valid against DuckDB, absence of disallowed verbs).
- Logged metadata (confidence, warnings, explanations) to help spot regressions in prompt behavior.

## Recommended cadence

- Run locally before cutting a release that changes prompts, schemas, or LLM provider settings.
- Schedule a nightly or pre-release pipeline stage that sets the required environment variables so prompt drift is caught early.

## Troubleshooting

- **Skipped tests**: confirm `A9_RUN_LLM_LIVE` and the API key env vars are present in the same shell running pytest.
- **Authentication errors**: verify the key is valid and the provider matches the configuration in `A9_Data_Product_Agent`.
- **SQL validation failures**: capture the generated SQL (pytest output logs it) and compare against the expected structure; adjust prompts or update the assertions as needed.
