import time

import prompt


def handle_db_errors(func):
    """Handle exceptions raised by database operations."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except KeyError as error:
            print(f"Ошибка: Таблица или столбец {error} не найден.")

        except ValueError as error:
            print(f"Ошибка валидации: {error}")

        except FileNotFoundError:
            print(
                "Ошибка: Файл данных не найден. "
                "Возможно, база данных не инициализирована."
            )

        return None

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__

    return wrapper


def confirm_action(action_name):
    """Request user confirmation before executing an operation."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            answer = prompt.string(
                f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
            )

            if answer != "y":
                return None

            return func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__

        return wrapper

    return decorator


def log_time(func):
    """Measure and display function execution time."""

    def wrapper(*args, **kwargs):
        start_time = time.monotonic()

        result = func(*args, **kwargs)

        elapsed_time = time.monotonic() - start_time
        print(f"Функция {func.__name__} выполнилась за {elapsed_time:.3f} секунд")

        return result

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__

    return wrapper


def create_cacher():
    """Create a function that caches results by key."""
    cache = {}

    def cache_result(key, value_func):
        if key not in cache:
            cache[key] = value_func()

        return cache[key]

    return cache_result
