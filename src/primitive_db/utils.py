import json
from pathlib import Path


def load_metadata(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)

    except FileNotFoundError:
        return {}


def save_metadata(filepath, data):
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(data, file)
