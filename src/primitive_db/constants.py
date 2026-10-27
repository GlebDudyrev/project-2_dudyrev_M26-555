from pathlib import Path


AVAILABLE_TYPES = {
    'int',
    'str',
    'bool'
}

USER_DATA_PATH = Path.home() / '.local' / 'share' / 'primitive_db'

METADATA_PATH = USER_DATA_PATH / "db_meta.json"
