# A9_LLM_Service_Agent PRD

## 1. Overview
Provides protocol-compliant, registry-controlled access to all supported LLM providers (OpenAI, Azure, Gemini, Anthropic, etc.) for Agent9. Enables prompt completion, summarization, and dynamic NLP query generation for analytics and conversational interfaces.

## 2. Modification History
- 2025-05-26: Initial PRD created for unified LLM service agent and dynamic NLP analytics support.

## 3. Problem Statement
- LLM access was fragmented across multiple modules and patterns, leading to duplication, maintainability issues, and non-compliance with Agent9 protocol and registry standards.

## 4. Goals & Success Criteria
- All LLM operations (completion, summarization, analytics parsing) are routed through this agent.
- Provider abstraction handled via `llm_factory.py`.
- Protocol compliance: All requests/responses use Pydantic models (`LLMRequest`/`LLMResponse`).
- Registry/orchestrator-controlled instantiation only.
- Supports dynamic NLP query parsing for analytics (business question → structured query params).
- Fully tested and documented.

## 5. Scope
- Unified LLM agent for all prompt-based operations in Agent9.
- Dynamic analytics question parsing for semantic query generation.
- Logging and error handling via shared logging utilities.

## 6. Out of Scope
- Direct instantiation by external scripts or agents.
- Non-English language support (MVP only).
- Advanced business logic beyond registry mapping.

## 7. Architecture & Design
- Uses `llm_factory.py` for provider abstraction.
- Exposes protocol entrypoint `invoke` (input: `LLMRequest`, output: `LLMResponse`).
- NLP analytics parsing method: `parse_analytics_question`.
- Instantiation via `create_from_registry` only.

## 8. Impact Analysis
- Deprecates direct use of provider modules in scripts/agents.
- Simplifies maintenance and onboarding.
- Ensures compliance with Agent9 agent/process rules.

## 9. Test Plan
- Unit tests for protocol entrypoint and analytics parsing.
- Integration tests with orchestrator/registry.
- Edge cases: ambiguous/invalid business questions, missing KPIs.

## 10. Documentation Updates
- Update agent card if config or protocol changes.
- Add onboarding and usage examples for analytics pipeline integration.

## 11. Affected Test Cases
- All LLM prompt/analytics operations must be updated to use this agent.
- Registry/orchestrator integration tests.

## 12. Pending Items
- Add/expand tests as new providers or analytics patterns are introduced.

---

## 13. Lessons Learned from LLM Service Agent Refactor
- **Protocol Compliance:** Strictly match method signatures, argument counts, and return types to protocol specs. Tests must assert on both single and batch scenarios.
- **YAML Frontmatter Hygiene:** Agent cards must have valid, Markdown-free YAML frontmatter. Use folded style (`>`) for long strings. Even minor formatting errors in YAML can break the test suite.
- **Async/Test Discipline:** All async agent/registry methods must be properly awaited in both implementation and tests. Inconsistent async usage leads to subtle bugs.
- **Loader/Test Robustness:** Loader utilities should parse only YAML, provide actionable errors, and assert presence/validity of all required cards and fields. Tests should fail fast and give clear guidance on card issues.
- **Incremental, Isolated Refactoring:** Refactor one agent/feature at a time, validate with focused tests, and only then move to the next. This avoids cascading failures and makes debugging easier.
- **Documentation Sync:** Always keep protocol, config, and card documentation in sync with code and tests to avoid drift and confusion.
