"""Helpers for storing metadata and records as JSON files."""

import json
import os

from .constants import TABLE_DATA_PATH


def load_metadata(filepath):
    """Load the table definitions, or return an empty mapping if absent."""
    try:
        with open(filepath, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_metadata(filepath, data):
    """Persist all table definitions to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False)


def load_table_data(table_name):
    """Load records for one table, or return an empty list if absent."""
    filepath = os.path.join(TABLE_DATA_PATH, f"{table_name}.json")
    try:
        with open(filepath, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_table_data(table_name, data):
    """Persist the records of one table to its JSON file."""
    os.makedirs(TABLE_DATA_PATH, exist_ok=True)
    filepath = os.path.join(TABLE_DATA_PATH, f"{table_name}.json")
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False)


def delete_table_data(table_name):
    """Remove one table's JSON file, if present."""
    filepath = os.path.join(TABLE_DATA_PATH, f"{table_name}.json")
    try:
        os.remove(filepath)
    except FileNotFoundError:
        pass
