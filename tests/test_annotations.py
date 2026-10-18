"""Evaluate every annotation in the package.

Python 3.14 evaluates annotations lazily, so mistakes such as a method named `list` shadowing the
builtin inside `list[...]` annotations only fail at import time on older versions (3.11-3.13).
Forcing evaluation here catches them on any interpreter.
"""

import importlib
import inspect
import pkgutil

import telegram_ai_bot


def _modules():
    for info in pkgutil.walk_packages(telegram_ai_bot.__path__, prefix="telegram_ai_bot."):
        if info.name.endswith("__main__"):
            continue
        yield importlib.import_module(info.name)


def _annotated_objects(module):
    for _, obj in inspect.getmembers(module):
        if getattr(obj, "__module__", None) != module.__name__:
            continue
        if inspect.isfunction(obj):
            yield obj
        elif inspect.isclass(obj):
            yield obj
            yield from (m for _, m in inspect.getmembers(obj, inspect.isfunction) if m.__module__ == module.__name__)


def test_all_annotations_evaluate():
    failures = []
    for module in _modules():
        for obj in _annotated_objects(module):
            try:
                inspect.get_annotations(obj, eval_str=True)
            except Exception as e:
                failures.append(f"{obj.__module__}.{obj.__qualname__}: {e!r}")
    assert not failures, "\n".join(failures)
