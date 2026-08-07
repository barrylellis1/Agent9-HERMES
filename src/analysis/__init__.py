"""
Agent9 Analysis Utilities

Deterministic measurement of Solution Finder output quality. Every function in
this package computes its result from data alone — arithmetic, set membership,
or registry lookup — with **no LLM call anywhere**.

That constraint is the point, not an implementation detail. These modules exist
to measure a stochastic process (SF synthesis on claude-sonnet-5, which cannot
even accept temperature=0). A model-based judge would wobble run-to-run and make
process noise indistinguishable from measurement noise. A stochastic ruler
cannot measure a stochastic process.

Modules:
- `mechanism`      — lever taxonomy + deterministic mechanism fingerprint
- `groundedness`   — G1-G6 per-option scoring against data + theory layer
- `problem_profile`— deterministic problem-type classification from DA output

See `DEVELOPMENT_PLAN.md` Phase 15 Stage H notes for the measurement design and
the findings that motivated it.
"""
