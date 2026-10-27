import prompt
import shlex

from .constants import METADATA_PATH
from .utils import load_metadata
from .utils import save_metadata
from .core import create_table
from .core import list_tables
from .core import drop_table


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

        try:
            args = shlex.split(prompt.string('>>> Введите команду: '))
        except ValueError:
            print('Некорректное команда. Попробуйте снова.')
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

            case (
                ['create_table', *_]
                | ['list_tables', *_]
                | ['drop_table', *_]
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
