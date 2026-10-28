from prettytable import PrettyTable

import prompt
import shlex

from .constants import METADATA_PATH
from .utils import load_metadata
from .utils import save_metadata
from .utils import load_table_data
from .utils import save_table_data
from .core import create_table
from .core import list_tables
from .core import drop_table
from .core import insert
from .core import select
from .core import update
from .core import delete
from .parser import parse_insert
from .parser import parse_select
from .parser import parse_update
from .parser import parse_delete


def _print_help():
    """Prints the help message for the current mode."""
   
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    
    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n") 


def _parse_columns(raw_columns):
    columns = []

    for column in raw_columns:
        if column.count(':') != 1:
            print(f'Некорректное значение: {column}. Попробуйте снова.')

            return None

        name, column_type = column.split(':')

        if not name or not column_type:
            print(f'Некорректное значение: {column}. Попробуйте снова.')

            return None

        columns.append((name, column_type))

    return columns


def run():
    _print_help()

    while True:
        need_save = False
        metadata = load_metadata(METADATA_PATH)

        user_input = prompt.string('>>> Введите команду: ')

        try:
            args = shlex.split(user_input)
        except ValueError:
            print('Некорректная команда. Попробуйте снова.')
            continue

        match args:
            case ['create_table', table_name, *raw_columns]:
                columns = _parse_columns(raw_columns)

                if columns is None:
                    continue

                metadata, need_save = create_table(metadata, table_name, columns)

            case ['list_tables']:
                list_tables(metadata)

            case ['drop_table', table_name]:
                metadata, need_save = drop_table(metadata, table_name)

            case ['help']:
                _print_help()

            case ['exit']:
                break

            case ['insert', *_]:
                parsed = parse_insert(user_input)

                if parsed is None:
                    continue

                table_name, values = parsed

                table_data = insert(metadata, table_name, values)

                if table_data is not None:
                    save_table_data(table_name, table_data)

            case ['select', *_]:
                parsed = parse_select(user_input)

                if parsed is None:
                    continue

                table_name, where_clause = parsed

                if table_name not in metadata:
                    print(f'Ошибка: Таблица "{table_name}" не существует.')
                    continue

                columns = [name for name, _ in metadata[table_name]]

                if where_clause is not None:
                    column = next(iter(where_clause))

                    if column not in columns:
                        print(f'Некорректное значение: столбец "{column}" не существует.')
                        continue

                table_data = load_table_data(table_name)
                records = select(table_data, where_clause)

                table = PrettyTable()
                table.field_names = columns

                for record in records:
                    table.add_row([record[name] for name in columns])

                print(table)

            case ['update', *_]:
                parsed = parse_update(user_input)

                if parsed is None:
                    continue

                table_name, set_clause, where_clause = parsed

                if table_name not in metadata:
                    print(f'Ошибка: Таблица "{table_name}" не существует.')
                    continue

                schema = dict(metadata[table_name])
                types = {'int': int, 'str': str, 'bool': bool}

                valid = True

                for clause in (set_clause, where_clause):
                    column, value = next(iter(clause.items()))

                    if column not in schema:
                        print(f'Некорректное значение: столбец "{column}" не существует.')
                        valid = False
                        break

                    if type(value) is not types[schema[column]]:
                        print(
                            f'Некорректное значение: {value}. '
                            f'Столбец "{column}" ожидает тип {schema[column]}.'
                        )
                        valid = False
                        break

                if not valid:
                    continue

                table_data = load_table_data(table_name)
                matched_records = select(table_data, where_clause)

                if not matched_records:
                    print('Записи, удовлетворяющие условию, не найдены.')
                    continue

                updated_ids = [record['ID'] for record in matched_records]

                updated_data = update(table_data, set_clause, where_clause)
                save_table_data(table_name, updated_data)

                for record_id in updated_ids:
                    print(
                        f'Запись с ID={record_id} в таблице '
                        f'"{table_name}" успешно обновлена.'
                    )

            case ['delete', *_]:
                parsed = parse_delete(user_input)

                if parsed is None:
                    continue

                table_name, where_clause = parsed

                if table_name not in metadata:
                    print(f'Ошибка: Таблица "{table_name}" не существует.')
                    continue

                schema = dict(metadata[table_name])
                column, value = next(iter(where_clause.items()))

                if column not in schema:
                    print(f'Некорректное значение: столбец "{column}" не существует.')
                    continue

                types = {'int': int, 'str': str, 'bool': bool}

                if type(value) is not types[schema[column]]:
                    print(
                        f'Некорректное значение: {value}. '
                        f'Столбец "{column}" ожидает тип {schema[column]}.'
                    )
                    continue

                table_data = load_table_data(table_name)
                matched_records = select(table_data, where_clause)

                if not matched_records:
                    print('Записи, удовлетворяющие условию, не найдены.')
                    continue

                deleted_ids = [record['ID'] for record in matched_records]

                updated_data = delete(table_data, where_clause)
                save_table_data(table_name, updated_data)

                for record_id in deleted_ids:
                    print(
                        f'Запись с ID={record_id} успешно удалена '
                        f'из таблицы "{table_name}".'
                    )

            case ['info', table_name]:
                if table_name not in metadata:
                    print(f'Ошибка: Таблица "{table_name}" не существует.')
                    continue

                columns = metadata[table_name]
                table_data = load_table_data(table_name)

                columns_info = ', '.join(
                    f'{name}:{dtype}'
                    for name, dtype in columns
                )

                print(f'Таблица: {table_name}')
                print(f'Столбцы: {columns_info}')
                print(f'Количество записей: {len(table_data)}')

            case (
                ['create_table', *_]
                | ['list_tables', *_]
                | ['drop_table', *_]
                | ['info', *_]
                | ['help', *_]
                | ['exit', *_]
            ):
                print(
                    'Некорректное значение: неверное количество аргументов. '
                    'Попробуйте снова.'
                )

            case [command, *_]:
                print(f'Функции <{command}> нет. Попробуйте снова.')

        if need_save:
            save_metadata(METADATA_PATH, metadata)
