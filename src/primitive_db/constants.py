import os

AVAILABLE_TYPES = {"int", "str", "bool"}

USER_DATA_PATH = os.path.join(
    os.path.expanduser("~"), ".local", "share", "primitive_db"
)
METADATA_PATH = os.path.join(USER_DATA_PATH, "db_meta.json")
TABLE_DATA_PATH = os.path.join(USER_DATA_PATH, "data")
