import os
import sys
import pytest

# Ensure the project root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_investor_data():
    return {
        "user_id": "user_1",
        "capital": 1000000,
        "risk_profile": "Moderate"
    }
