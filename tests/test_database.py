"""Self-contained black-box checks for the console database (no pytest required)."""

import io
import json
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from primitive_db import core, engine, parser, utils


def run_commands(root, commands):
    """Execute a console session with actual JSON storage in an isolated directory."""
    meta_path = root / "db_meta.json"
    data_path = root / "data"
    output = io.StringIO()
    with (
        patch.object(core, "METADATA_PATH", meta_path),
        patch.object(utils, "TABLE_DATA_PATH", data_path),
        patch.object(engine.prompt, "string", side_effect=[*commands, "exit"]),
        redirect_stdout(output),
    ):
        engine.run()
    return output.getvalue()


def metadata(root):
    filepath = root / "db_meta.json"
    return json.loads(filepath.read_text(encoding="utf-8")) if filepath.exists() else {}


def records(root, table):
    filepath = root / "data" / f"{table}.json"
    return json.loads(filepath.read_text(encoding="utf-8")) if filepath.exists() else []


def test_example_complete(root):
    out = run_commands(
        root,
        [
            "create_table users name:str age:int is_active:bool",
            'insert into users values ("Sergei", 28, true)',
            "select from users where age = 28",
            'update users set age = 29 where name = "Sergei"',
            "delete from users where ID = 1",
            "info users",
        ],
    )
    assert (
        'Таблица "users" успешно создана со столбцами: '
        "ID:int, name:str, age:int, is_active:bool"
    ) in out
    assert 'Запись с ID=1 успешно добавлена в таблицу "users".' in out
    assert "| ID |" in out and "Sergei" in out
    assert 'Запись с ID=1 в таблице "users" успешно обновлена.' in out
    assert 'Запись с ID=1 успешно удалена из таблицы "users".' in out
    assert "Количество записей: 0" in out
    assert records(root, "users") == []


def test_schema_and_duplicate_create(root):
    out = run_commands(
        root,
        [
            "create_table users name:str age:int",
            "create_table users name:str",
            "list_tables",
        ],
    )
    assert 'Ошибка: Таблица "users" уже существует.' in out
    assert out.count("- users\n") == 1
    assert metadata(root)["users"] == [["ID", "int"], ["name", "str"], ["age", "int"]]


def test_id_schema_order_and_type(root):
    out = run_commands(
        root,
        [
            "create_table users name:str ID:int age:int",
            'insert into users values ("Ada", 21)',
        ],
    )
    assert "ID:int, name:str, age:int" in out
    assert list(records(root, "users")[0]) == ["ID", "name", "age"]
    assert records(root, "users")[0]["ID"] == 1


def test_missing_schema_and_invalid_types(root):
    out = run_commands(
        root,
        [
            "create_table a value:float",
            "create_table b ID:str name:str",
            "create_table c name:str name:int",
            "create_table d name",
            "create_table e name:str",
        ],
    )
    assert "Некорректное значение: value:float." in out
    assert "Некорректное значение: ID:str." in out
    assert "повторяющийся столбец name" in out
    assert "Некорректное значение: name." in out
    assert list(metadata(root)) == ["e"]


def test_required_values_and_type_validation(root):
    out = run_commands(
        root,
        [
            "create_table users name:str age:int active:bool",
            'insert into users values ("Joe", 30)',
            'insert into users values ("Joe", "30", True)',
            'insert into users values ("Joe", true, true)',
            'insert into users values ("Joe", 30, true)',
        ],
    )
    assert "количество значений не соответствует количеству столбцов" in out
    assert 'Столбец "age" ожидает тип int.' in out
    assert len(records(root, "users")) == 1


def test_boolean_spelling_and_quoted_boolean(root):
    out = run_commands(
        root,
        [
            "create_table flags enabled:bool",
            "insert into flags values (TRUE)",
            "insert into flags values (false)",
            "insert into flags values (TrUe)",
            'insert into flags values ("true")',
        ],
    )
    assert 'Столбец "enabled" ожидает тип bool.' in out
    assert [x["enabled"] for x in records(root, "flags")] == [True, False, True]


def test_bool_int_distinction_in_where(root):
    out = run_commands(
        root,
        [
            "create_table t enabled:bool age:int",
            "insert into t values (TRUE, 1)",
            "select from t where enabled = 1",
            "select from t where age = TRUE",
            "update t set age = 2 where enabled = 1",
            "delete from t where enabled = 1",
        ],
    )
    assert out.count("ожидает тип bool.") >= 3
    assert "ожидает тип int." in out
    assert records(root, "t") == [{"ID": 1, "enabled": True, "age": 1}]


def test_id_immutable(root):
    out = run_commands(
        root,
        [
            "create_table t name:str",
            'insert into t values ("A")',
            'insert into t values ("B")',
            "update t set ID = 1 where ID = 2",
        ],
    )
    assert "ID нельзя изменять." in out
    assert [r["ID"] for r in records(root, "t")] == [1, 2]


def test_update_multiple_matches_and_persistence(root):
    out = run_commands(
        root,
        [
            "create_table t age:int active:bool",
            "insert into t values (21, true)",
            "insert into t values (21, false)",
            "insert into t values (35, true)",
            "update t set age = 22 where age = 21",
        ],
    )
    assert out.count('в таблице "t" успешно обновлена.') == 2
    assert [r["age"] for r in records(root, "t")] == [22, 22, 35]


def test_delete_multiple_matches(root):
    out = run_commands(
        root,
        [
            "create_table t age:int",
            "insert into t values (5)",
            "insert into t values (5)",
            "insert into t values (6)",
            "delete from t where age = 5",
        ],
    )
    assert out.count('успешно удалена из таблицы "t".') == 2
    assert [r["ID"] for r in records(root, "t")] == [3]


def test_drop_recreate_and_data_cleanup(root):
    out = run_commands(
        root,
        [
            "create_table t name:str",
            'insert into t values ("A")',
            "drop_table t",
            "create_table t age:int",
            "select from t",
            "info t",
        ],
    )
    assert "Количество записей: 0" in out
    assert records(root, "t") == []
    assert not (root / "data" / "t.json").exists()
    assert metadata(root)["t"] == [["ID", "int"], ["age", "int"]]


def test_drop_unstored_and_nonexistent(root):
    out = run_commands(
        root,
        [
            "create_table unused name:str",
            "drop_table unused",
            "drop_table absent",
            "create_table again name:str",
        ],
    )
    assert 'Таблица "unused" успешно удалена.' in out
    assert 'Ошибка: Таблица "absent" не существует.' in out
    assert "again" in metadata(root)


def test_missing_tables(root):
    out = run_commands(
        root,
        [
            'insert into none values ("A")',
            "select from none",
            "update none set age = 2 where ID = 1",
            "delete from none where ID = 1",
            "info none",
        ],
    )
    assert out.count('Таблица "none" не существует.') == 5
    assert not (root / "data" / "none.json").exists()


def test_missing_columns_and_bad_clause_types(root):
    out = run_commands(
        root,
        [
            "create_table t age:int",
            "insert into t values (20)",
            "select from t where missing = 1",
            'update t set age = "bad" where ID = 1',
            "update t set missing = 2 where ID = 1",
            "delete from t where missing = 2",
        ],
    )
    assert out.count('столбец "missing" не существует.') == 3
    assert 'Столбец "age" ожидает тип int.' in out
    assert records(root, "t")[0]["age"] == 20


def test_string_with_comma_equals_and_keyword_where(root):
    out = run_commands(
        root,
        [
            "create_table t name:str",
            'insert into t values ("A, B")',
            'update t set name = "A where B = C" where name = "A, B"',
            'select from t where name = "A where B = C"',
        ],
    )
    assert "успешно обновлена." in out
    assert "A where B = C" in out
    assert records(root, "t")[0]["name"] == "A where B = C"


def test_bad_syntax_and_followup_survive(root):
    out = run_commands(
        root,
        [
            "nonexistent_cmd",
            "create_table t age",
            'insert into t values ("unterminated)',
            "update t set age = 1",
            "delete from t",
            "select from t where age",
            "help extra",
            "",
            "create_table t age:int",
            "insert into t values (18)",
        ],
    )
    assert "Функции <nonexistent_cmd> нет. Попробуйте снова." in out
    assert "Некорректная команда. Попробуйте снова." in out
    assert "Некорректная команда update." in out
    assert "Некорректная команда delete." in out
    assert len(records(root, "t")) == 1


def test_persistence_across_sessions(root):
    run_commands(root, ["create_table t name:str", 'insert into t values ("One")'])
    out = run_commands(
        root, ["select from t", 'insert into t values ("Two")', "info t"]
    )
    assert "One" in out
    assert "Запись с ID=2" in out
    assert "Количество записей: 2" in out


def test_id_after_deletion(root):
    run_commands(
        root,
        [
            "create_table t name:str",
            'insert into t values ("A")',
            'insert into t values ("B")',
            'insert into t values ("C")',
            "delete from t where ID = 2",
            'insert into t values ("D")',
        ],
    )
    assert [r["ID"] for r in records(root, "t")] == [1, 3, 4]


def test_empty_table_read(root):
    out = run_commands(root, ["create_table t age:int", "select from t", "info t"])
    assert "| ID | age |" in out
    assert "Количество записей: 0" in out
    assert not (root / "data" / "t.json").exists()


def test_no_data_writes_on_invalid_update_delete(root):
    run_commands(root, ["create_table t age:int", "insert into t values (1)"])
    path = root / "data" / "t.json"
    before = path.read_bytes()
    out = run_commands(
        root,
        [
            'update t set age = "nope" where ID = 1',
            "delete from t where ID = 999",
            "update t set age = 20 where ID = 999",
        ],
    )
    assert "не найдены." in out
    assert path.read_bytes() == before


def test_only_expected_table_files(root):
    run_commands(
        root,
        [
            "create_table users name:str",
            "create_table other age:int",
            'insert into users values ("Z")',
        ],
    )
    assert {p.name for p in (root / "data").iterdir()} == {"users.json"}
    assert set(metadata(root)) == {"users", "other"}


def test_parser_types():
    assert parser.parse_where("age = 28") == {"age": 28}
    assert parser.parse_set("active = FALSE") == {"active": False}
    assert parser.parse_where('name = "28"') == {"name": "28"}
    assert parser.parse_where('name = "true"') == {"name": "true"}
    assert parser.parse_insert('insert into t values ("A, B", -1, TrUe)') == (
        "t",
        ["A, B", -1, True],
    )
    assert parser.parse_update('update t set name = "A where B" where ID = 1') == (
        "t",
        {"name": "A where B"},
        {"ID": 1},
    )


def test_help_includes_all_commands(root):
    out = run_commands(root, ["help"])
    for name in (
        "create_table",
        "drop_table",
        "list_tables",
        "insert",
        "select",
        "update",
        "delete",
        "info",
        "help",
        "exit",
    ):
        assert name in out


def test_input_names_do_not_escape_data_directory(root):
    out = run_commands(
        root, ["create_table ../other name:str", "create_table safe name:str"]
    )
    assert "Некорректное значение" in out
    assert set(metadata(root)) == {"safe"}


def test_insert_one_record_only(root):
    out = run_commands(
        root,
        [
            "create_table t name:str age:int",
            'insert into t values ("A", 10), ("B", 20)',
        ],
    )
    assert "Некорректное значение" in out
    assert records(root, "t") == []


def run_all():
    tests = [
        (name, obj)
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    succeeded = 0
    for name, func in tests:
        with tempfile.TemporaryDirectory(prefix="primitive_db_test_") as directory:
            if name == "test_parser_types":
                func()
            else:
                func(Path(directory))
        succeeded += 1
        print(f"PASS {name}")
    print(f"RESULT {succeeded}/{len(tests)} passed")


if __name__ == "__main__":
    run_all()
