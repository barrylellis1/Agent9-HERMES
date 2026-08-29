"""Pure, stateless validators over registry records.

No agent instantiation, no LLM calls, no DB access -- these take already-loaded
Pydantic models / dicts and return findings. Callers (scripts, agents) decide
what to do with the result (log, raise, block registration).
"""
