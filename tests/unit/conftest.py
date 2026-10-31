import sys

import pytest


@pytest.fixture(autouse=True)
def _fresh_market_analysis_reuse():
    """Market Analysis keeps answers for 24 hours in a module-level store (2026-10-30). Clear it
    around every test so one test's answer is never another test's input."""
    mod = sys.modules.get("src.agents.new.a9_market_analysis_agent")
    if mod is not None:
        mod._REUSE.clear()
    yield
    mod = sys.modules.get("src.agents.new.a9_market_analysis_agent")
    if mod is not None:
        mod._REUSE.clear()
