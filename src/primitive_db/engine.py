import shlex

import prompt

from . import core, parser


def _print_help():
    """Display all supported commands."""
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("\n***Операции с данными***")
    print("Функции:")
    print(
        "<command> insert into <имя_таблицы> values (<значение1>, ...) "
        "- создать запись."
    )
    print(
        "<command> select from <имя_таблицы> where <столбец> = <значение> "
        "- прочитать записи по условию."
    )
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    print(
        "<command> update <имя_таблицы> set <столбец> = <значение> "
        "where <столбец> = <значение> - обновить запись."
    )
    print(
        "<command> delete from <имя_таблицы> where <столбец> = <значение> "
        "- удалить запись."
    )
    print("<command> info <имя_таблицы> - вывести информацию о таблице.")
    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def run():
    """Read user commands and dispatch them through the appropriate parser."""
    _print_help()
    while True:
        user_input = prompt.string(">>> Введите команду: ")
        try:
            args = shlex.split(user_input)
        except ValueError:
            print("Некорректная команда. Попробуйте снова.")
            continue

        match args:
            case ["create_table", *_]:
                parsed = parser.parse_create_table(args)
                if parsed is not None:
                    table_name, columns = parsed
                    core.create_table(
                        table_name=table_name,
                        columns=columns,
                    )

            case ["drop_table", *_]:
                parsed = parser.parse_table_name(args)
                if parsed is not None:
                    table_name = parsed
                    core.drop_table(table_name)

            case ["list_tables"]:
                core.list_tables()

            case ["insert", *_]:
                parsed = parser.parse_insert(user_input)
                if parsed is not None:
                    table_name, values = parsed
                    core.insert(
                        table_name=table_name,
                        values=values,
                    )

            case ["select", *_]:
                parsed = parser.parse_select(user_input)
                if parsed is not None:
                    table_name, where_clause = parsed
                    core.select(
                        table_name=table_name,
                        where_clause=where_clause,
                    )

            case ["update", *_]:
                parsed = parser.parse_update(user_input)
                if parsed is not None:
                    table_name, set_clause, where_clause = parsed
                    core.update(
                        table_name=table_name,
                        set_clause=set_clause,
                        where_clause=where_clause,
                    )

            case ["delete", *_]:
                parsed = parser.parse_delete(user_input)
                if parsed is not None:
                    table_name, where_clause = parsed
                    core.delete(
                        table_name=table_name,
                        where_clause=where_clause,
                    )

            case ["info", *_]:
                parsed = parser.parse_table_name(args)
                if parsed is not None:
                    table_name = parsed
                    core.info(table_name=table_name)

            case ["help"]:
                _print_help()

            case ["exit"]:
                return

            case ["list_tables", *_] | ["help", *_] | ["exit", *_]:
                print(
                    "Некорректное значение: неверное количество аргументов. "
                    "Попробуйте снова."
                )

            case []:
                print("Некорректное значение: пустая команда. Попробуйте снова.")

            case [command, *_]:
                print(f"Функции <{command}> нет. Попробуйте снова.")
