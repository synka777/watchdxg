# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    # Create a directory for storing the state
    profile_dir = Path(__file__).parent / "playwright_profile"
    profile_dir.mkdir(exist_ok=True)

    # Path to the JSON file for storage state
    storage_file = profile_dir / "storage_state.json"
    if not storage_file.exists():
        # Initialize with empty state
        storage_file.write_text("{}")

    return {
        **browser_context_args,
        "storage_state": str(storage_file),   # Must be a file path string
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) "
            "Gecko/20100101 Firefox/119.0"
        ),
        "ignore_https_errors": True,
    }
