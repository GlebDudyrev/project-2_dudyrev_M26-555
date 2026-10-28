from .constants import AVAILABLE_TYPES
from .utils import load_table_data


def create_table(
    metadata,
    table_name,
    columns,
):  
    if not table_name:
        print('Некорректное значение: пустое имя таблицы.')

        return metadata, False

    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')

        return metadata, False

    if not columns:
        print('Некорректное значение: не указаны столбцы. Попробуйте снова.')

        return metadata, False

    names = set()
    for column_name, column_type in columns:
        if (
            column_type not in AVAILABLE_TYPES
            or column_name == 'ID' and column_type != 'int'
        ):
            print(f'Некорректное значение: {column_name}:{column_type}. Попробуйте снова.')

            return metadata, False

        if column_name in names:
            print(f'Некорректное значение: повторяющийся столбец {column_name}.')

            return metadata, False

        names.add(column_name)

    columns = [
        ('ID', 'int'),
        *((name, dtype) for name, dtype in columns if name != 'ID'),
    ]

    metadata[table_name] = columns

    print(
        f'Таблица "{table_name}" успешно создана со столбцами:',
        ', '.join(f'{name}:{type}' for name, type in columns)
    )

    return metadata, True


def list_tables(metadata):
    for table_name in metadata.keys():
        print(f'- {table_name}')


def drop_table(
    metadata,
    table_name,
):
    if not table_name:
        print('Некорректное значение: пустое имя таблицы.')

        return metadata, False

    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')

        return metadata, False

    del metadata[table_name]

    print(f'Таблица "{table_name}" успешно удалена.')

    return metadata, True


def insert(metadata, table_name, values):
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return None

    columns = [
        (name, dtype)
        for name, dtype in metadata[table_name]
        if name != 'ID'
    ]

    if len(values) != len(columns):
        print(
            'Некорректное значение: количество значений '
            'не соответствует количеству столбцов.'
        )
        return None

    types = {
        'int': int,
        'str': str,
        'bool': bool,
    }

    for (column_name, column_type), value in zip(columns, values):
        if type(value) is not types[column_type]:
            print(
                f'Некорректное значение: {value}. '
                f'Столбец "{column_name}" ожидает тип {column_type}.'
            )
            return None

    data = load_table_data(table_name)

    new_id = max((record['ID'] for record in data), default=0) + 1

    record = {'ID': new_id}
    record.update(
        (name, value)
        for (name, _), value in zip(columns, values)
    )

    data.append(record)

    print(
        f'Запись с ID={new_id} успешно добавлена '
        f'в таблицу "{table_name}".'
    )

    return data


def select(table_data, where_clause=None):
    if where_clause is None:
        return table_data

    return [
        record
        for record in table_data
        if all(
            record.get(column) == value
            for column, value in where_clause.items()
        )
    ]


def update(table_data, set_clause, where_clause):
    for record in select(table_data, where_clause):
        record.update(set_clause)

    return table_data


def delete(table_data, where_clause):
    table_data[:] = [
        record
        for record in table_data
        if not all(
            record.get(column) == value
            for column, value in where_clause.items()
        )
    ]

    return table_data
