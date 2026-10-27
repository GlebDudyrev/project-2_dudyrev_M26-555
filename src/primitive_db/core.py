from .constants import AVAILABLE_TYPES


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
