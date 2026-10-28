import json
from pathlib import Path

from .constants import TABLE_DATA_PATH


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


def load_table_data(table_name):
    filepath = TABLE_DATA_PATH / f'{table_name}.json'

    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_table_data(table_name, data):
    filepath = TABLE_DATA_PATH / f'{table_name}.json'
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(data, file)
