from prettytable import PrettyTable

from .constants import AVAILABLE_TYPES, METADATA_PATH, PYTHON_TYPES
from .decorators import handle_db_errors, confirm_action, log_time, create_cacher
from .utils import (
    delete_table_data,
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)


_select_cache = create_cacher()


def _invalidate_select_cache():
    """Invalidate all cached SELECT results."""
    global _select_cache
    _select_cache = create_cacher()


def _get_schema(metadata, table_name):
    """Return a table schema, reporting a missing table to the user."""

    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return None

    return dict(metadata[table_name])


def _validate_clause(schema, clause):
    """Check that field names and value types match the table schema."""

    for column, value in clause.items():
        if column not in schema:
            print(f'Некорректное значение: столбец "{column}" не существует.')
            return False

        expected = PYTHON_TYPES[schema[column]]
        if type(value) is not expected:
            print(
                f"Некорректное значение: {value}. "
                f'Столбец "{column}" ожидает тип {schema[column]}.'
            )
            return False

    return True


def _matches(record, where_clause):
    """Match a record without treating bool and int as the same type."""

    return all(
        column in record
        and type(record[column]) is type(value)
        and record[column] == value
        for column, value in where_clause.items()
    )


def _select_records(table_data, where_clause=None):
    """Return all records or those matching the given condition."""

    if where_clause is None:
        return table_data

    return [record for record in table_data if _matches(record, where_clause)]


@handle_db_errors
def create_table(table_name, columns):
    """Create a table definition. The ID column is added automatically."""

    metadata = load_metadata(METADATA_PATH)

    if not table_name:
        print("Некорректное значение: пустое имя таблицы. Попробуйте снова.")
        return None

    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return None

    if not columns:
        print("Некорректное значение: не указаны столбцы. Попробуйте снова.")
        return None

    names = set()
    for name, dtype in columns:
        if (
            not name
            or dtype not in AVAILABLE_TYPES
            or (name == "ID" and dtype != "int")
        ):
            print(f"Некорректное значение: {name}:{dtype}. Попробуйте снова.")
            return None

        if name in names:
            print(f"Некорректное значение: повторяющийся столбец {name}.")
            return None

        names.add(name)

    metadata[table_name] = [
        ("ID", "int"),
        *((name, dtype) for name, dtype in columns if name != "ID"),
    ]
    save_metadata(METADATA_PATH, metadata)
    _invalidate_select_cache()

    description = ", ".join(f"{name}:{dtype}" for name, dtype in metadata[table_name])
    print(f'Таблица "{table_name}" успешно создана со столбцами: {description}')

    return metadata


@handle_db_errors
def list_tables():
    """Display the names of all defined tables."""

    metadata = load_metadata(METADATA_PATH)
    for table_name in metadata:
        print(f"- {table_name}")

    return list(metadata)


@handle_db_errors
@confirm_action('удаление таблицы')
def drop_table(table_name):
    """Remove a table definition and its associated data file."""

    metadata = load_metadata(METADATA_PATH)
    if _get_schema(metadata, table_name) is None:
        return None

    delete_table_data(table_name)
    del metadata[table_name]

    save_metadata(METADATA_PATH, metadata)
    _invalidate_select_cache()

    print(f'Таблица "{table_name}" успешно удалена.')

    return metadata


@handle_db_errors
@log_time
def insert(table_name, values):
    """Validate and append one record with an automatically generated ID."""

    metadata = load_metadata(METADATA_PATH)
    schema = _get_schema(metadata, table_name)
    if schema is None:
        return None

    columns = [(name, dtype) for name, dtype in metadata[table_name] if name != "ID"]
    if len(values) != len(columns):
        print(
            "Некорректное значение: количество значений "
            "не соответствует количеству столбцов."
        )
        return None

    for (name, dtype), value in zip(columns, values):
        if type(value) is not PYTHON_TYPES[dtype]:
            print(
                f'Некорректное значение: {value}. Столбец "{name}" ожидает тип {dtype}.'
            )
            return None

    table_data = load_table_data(table_name)

    new_id = max((record["ID"] for record in table_data), default=0) + 1

    record = {"ID": new_id}
    record.update((name, value) for (name, _), value in zip(columns, values))

    table_data.append(record)
    save_table_data(table_name, table_data)
    _invalidate_select_cache()

    print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')

    return table_data


@handle_db_errors
@log_time
def select(table_name, where_clause=None):
    """Validate the query and display matching records using PrettyTable."""

    metadata = load_metadata(METADATA_PATH)
    schema = _get_schema(metadata, table_name)

    if schema is None:
        return None

    if where_clause is not None and not _validate_clause(schema, where_clause):
        return None

    cache_key = (
        table_name,
        None if where_clause is None else tuple(sorted(where_clause.items())),
    )

    selected = _select_cache(
        cache_key,
        lambda: _select_records(
            load_table_data(table_name),
            where_clause,
        ),
    )

    table = PrettyTable()
    table.field_names = list(schema)

    for record in selected:
        table.add_row([record[column] for column in schema])

    print(table)

    return selected


@handle_db_errors
def update(table_name, set_clause, where_clause):
    """Update matching records while preserving field types and unique IDs."""

    metadata = load_metadata(METADATA_PATH)
    schema = _get_schema(metadata, table_name)

    if schema is None:
        return None

    if not _validate_clause(schema, set_clause) or not _validate_clause(
        schema, where_clause
    ):
        return None

    if "ID" in set_clause:
        print("Некорректное значение: ID нельзя изменять. Попробуйте снова.")
        return None

    table_data = load_table_data(table_name)
    matching = _select_records(table_data, where_clause)

    if not matching:
        print("Записи, удовлетворяющие условию, не найдены.")
        return None

    ids = [record["ID"] for record in matching]
    for record in matching:
        record.update(set_clause)

    save_table_data(table_name, table_data)
    _invalidate_select_cache()

    for record_id in ids:
        print(f'Запись с ID={record_id} в таблице "{table_name}" успешно обновлена.')

    return table_data


@handle_db_errors
@confirm_action("удаление записей")
def delete(table_name, where_clause):
    """Remove all records matching a validated condition."""

    metadata = load_metadata(METADATA_PATH)
    schema = _get_schema(metadata, table_name)

    if schema is None:
        return None

    if not _validate_clause(schema, where_clause):
        return None

    table_data = load_table_data(table_name)
    matching = _select_records(table_data, where_clause)

    if not matching:
        print("Записи, удовлетворяющие условию, не найдены.")
        return None

    deleted_ids = [record["ID"] for record in matching]
    table_data[:] = [
        record for record in table_data if not _matches(record, where_clause)
    ]

    save_table_data(table_name, table_data)
    _invalidate_select_cache()

    for record_id in deleted_ids:
        print(f'Запись с ID={record_id} успешно удалена из таблицы "{table_name}".')

    return table_data


@handle_db_errors
def info(table_name):
    """Display table name, columns and current number of records."""

    metadata = load_metadata(METADATA_PATH)

    if _get_schema(metadata, table_name) is None:
        return None

    columns = metadata[table_name]
    count = len(load_table_data(table_name))
    column_info = ", ".join(f"{name}:{dtype}" for name, dtype in columns)

    print(f"Таблица: {table_name}")
    print(f"Столбцы: {column_info}")
    print(f"Количество записей: {count}")

    return count
