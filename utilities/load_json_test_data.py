# utilities/load_json_test_data.py
import json
from pathlib import Path


def read_json(filename: str) -> dict:
    """Loads and parses a JSON file located at the project root (e.g.
    'test_data.json'), regardless of the current working directory the
    test run was invoked from."""
    root_dir = Path(__file__).resolve().parent.parent
    file_path = root_dir / filename
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
