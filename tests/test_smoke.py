"""
Simple smoke test to verify that the pytest environment is working properly.
"""

import os
import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def test_environment_setup():
    """Test that the environment is set up correctly."""
    assert os.path.exists(".env"), ".env file should exist"
    assert "OPENAI_API_KEY" in os.environ, "OPENAI_API_KEY should be in environment variables"


def test_basic_functionality():
    """Test basic Python functionality."""
    assert 1 + 1 == 2, "Basic arithmetic should work"
    assert "hello".upper() == "HELLO", "String methods should work"


def test_import_dependencies():
    """Test that we can import key dependencies."""
    try:
        import pandas as pd
        import numpy as np
        import duckdb
        from fastapi import FastAPI
        from pydantic import BaseModel
        
        assert pd.__name__ == "pandas", "Should import pandas correctly"
        assert np.__name__ == "numpy", "Should import numpy correctly"
        assert duckdb.__name__ == "duckdb", "Should import duckdb correctly"
        assert FastAPI.__name__ == "FastAPI", "Should import FastAPI correctly"
        assert BaseModel.__name__ == "BaseModel", "Should import Pydantic BaseModel correctly"
    except ImportError as e:
        pytest.fail(f"Failed to import dependency: {e}")
