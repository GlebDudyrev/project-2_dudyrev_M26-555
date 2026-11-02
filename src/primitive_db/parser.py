def _invalid(value):
    print(f'Некорректное значение: {value}. Попробуйте снова.')
    return None


def _parse_table_name(table_name):
    """Validate a simple identifier used for a table name."""

    if not table_name.isidentifier():
        return _invalid(table_name)

    return table_name


def parse_create_table(args):
    """Parse the table name and its column:type declarations."""

    if len(args) < 2:
        print(
            'Некорректное значение: неверное количество аргументов. Попробуйте снова.'
        )
        return None

    table_name = _parse_table_name(args[1])
    if table_name is None:
        return None

    columns = []
    for raw_column in args[2:]:
        if raw_column.count(':') != 1:
            return _invalid(raw_column)

        name, dtype = raw_column.split(':', maxsplit=1)
        if not name.isidentifier() or not dtype:
            return _invalid(raw_column)

        columns.append((name, dtype))

    return table_name, columns


def parse_table_name(args):
    """Parse a command requiring exactly one table-name argument."""

    if len(args) != 2:
        print(
            'Некорректное значение: неверное количество аргументов. Попробуйте снова.'
        )
        return None

    return _parse_table_name(args[1])


def _parse_value(raw_value):
    """Parse a quoted string, case-insensitive bool or integer."""

    raw_value = raw_value.strip()
    if (
        len(raw_value) >= 2
        and raw_value[0] == raw_value[-1]
        and raw_value[0] in ('"', "'")
    ):
        return raw_value[1:-1]

    if raw_value.lower() == 'true':
        return True

    if raw_value.lower() == 'false':
        return False

    try:
        return int(raw_value)
    except ValueError:
        return None


def _parse_assignment(expression):
    parts = expression.split('=', maxsplit=1)

    if len(parts) != 2:
        return _invalid(expression)

    column, raw_value = map(str.strip, parts)
    if not column.isidentifier() or not raw_value:
        return _invalid(expression)

    value = _parse_value(raw_value)
    if value is None:
        return _invalid(raw_value)

    return {column: value}


def parse_where(expression):
    """Parse a WHERE equality expression."""
    return _parse_assignment(expression)


def parse_set(expression):
    """Parse a SET assignment expression."""
    return _parse_assignment(expression)


def _split_values(expression):
    """Split comma-separated values without splitting inside quoted strings."""

    values = []
    start = 0
    quote = None

    for index, char in enumerate(expression):
        if char in ('"', "'"):
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
        elif char == ',' and quote is None:
            values.append(expression[start:index].strip())
            start = index + 1

    if quote is not None:
        print('Некорректное значение: незакрытые кавычки.')
        return None

    values.append(expression[start:].strip())

    return values


def parse_insert(command):
    """Parse INSERT with one parenthesized record of typed values."""

    parts = command.strip().split(maxsplit=3)
    if len(parts) != 4 or parts[:2] != ['insert', 'into']:
        print('Некорректная команда insert. Попробуйте снова.')
        return None

    table_name = _parse_table_name(parts[2])
    if table_name is None:
        return None

    tail = parts[3]
    if not tail.startswith('values'):
        print('Некорректная команда insert. Попробуйте снова.')
        return None

    tail = tail[len('values') :].strip()
    if not tail.startswith('(') or not tail.endswith(')'):
        print('Некорректная команда insert. Попробуйте снова.')
        return None

    values = _split_values(tail[1:-1])
    if values is None:
        return None

    result = []
    for raw_value in values:
        value = _parse_value(raw_value)

        if value is None:
            return _invalid(raw_value)

        result.append(value)

    return table_name, result


def parse_select(command):
    """Parse SELECT with an optional WHERE equality expression."""

    parts = command.strip().split(maxsplit=3)
    if len(parts) < 3 or parts[:2] != ['select', 'from']:
        print('Некорректная команда select. Попробуйте снова.')
        return None

    table_name = _parse_table_name(parts[2])
    if table_name is None:
        return None

    if len(parts) == 3:
        return table_name, None

    condition = parts[3].split(maxsplit=1)
    if len(condition) != 2 or condition[0] != 'where':
        print('Некорректная команда select. Попробуйте снова.')
        return None

    where_clause = parse_where(condition[1])
    if where_clause is None:
        return None

    return table_name, where_clause


def _split_where_outside_quotes(expression):
    """Split at the WHERE keyword, ignoring occurrences inside quoted strings."""

    quote = None
    for index, char in enumerate(expression):
        if char in (''', '''):
            if quote is None:
                quote = char
            elif quote == char:
                quote = None

        if quote is None and char.isspace():
            rest = expression[index:].lstrip()
            if rest.startswith('where') and len(rest) > 5 and rest[5].isspace():
                return expression[:index], rest[5:].strip()

    return None


def parse_update(command):
    """Parse UPDATE with one SET and one WHERE assignment."""

    parts = command.strip().split(maxsplit=3)
    if len(parts) != 4 or parts[0] != 'update' or parts[2] != 'set':
        print('Некорректная команда update. Попробуйте снова.')
        return None

    table_name = _parse_table_name(parts[1])
    if table_name is None:
        return None

    clauses = _split_where_outside_quotes(parts[3])
    if clauses is None:
        print('Некорректная команда update. Попробуйте снова.')
        return None

    set_clause = parse_set(clauses[0])
    if set_clause is None:
        return None

    where_clause = parse_where(clauses[1])
    if where_clause is None:
        return None

    return table_name, set_clause, where_clause


def parse_delete(command):
    """Parse DELETE with one WHERE equality expression."""

    parts = command.strip().split(maxsplit=3)
    if len(parts) != 4 or parts[:2] != ['delete', 'from']:
        print('Некорректная команда delete. Попробуйте снова.')
        return None

    table_name = _parse_table_name(parts[2])
    if table_name is None:
        return None

    condition = parts[3].split(maxsplit=1)
    if len(condition) != 2 or condition[0] != 'where':
        print('Некорректная команда delete. Попробуйте снова.')
        return None

    where_clause = parse_where(condition[1])
    if where_clause is None:
        return None

    return table_name, where_clause
