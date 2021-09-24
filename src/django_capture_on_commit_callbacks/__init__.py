from contextlib import contextmanager
from typing import Any, Callable, ContextManager, Generator, List

import django
from django.core.exceptions import ImproperlyConfigured
from django.db import DEFAULT_DB_ALIAS, connections


def check_django_version() -> None:
    if django.VERSION >= (3, 2):
        raise ImproperlyConfigured(
            "django-capture-on-commit-callbacks is unnecessary on Django "
            + "3.2+. The functionality has been merged as "
            + "TestCase.captureOnCommitCallbacks()"
        )


@contextmanager
def capture_on_commit_callbacks(
    *, using: str = DEFAULT_DB_ALIAS, execute: bool = False
) -> Generator[List[Callable[[], None]], None, None]:
    check_django_version()

    callbacks: List[Callable[[], None]] = []
    start_count = len(connections[using].run_on_commit)
    try:
        yield callbacks
    finally:
        callback_count = len(connections[using].run_on_commit)
        while True:
            run_on_commit = connections[using].run_on_commit[start_count:]
            callbacks[:] = [func for sids, func in run_on_commit]
            if execute:
                for callback in callbacks:
                    callback()

            if callback_count == len(connections[using].run_on_commit):
                break
            start_count = callback_count - 1
            callback_count = len(connections[using].run_on_commit)


class TestCaseMixin:
    @classmethod
    def __init_subclass__(cls, *args: Any, **kwargs: Any) -> None:
        check_django_version()
        super().__init_subclass__(*args, **kwargs)  # type: ignore [call-arg]

    @classmethod
    def captureOnCommitCallbacks(
        cls, *, using: str = DEFAULT_DB_ALIAS, execute: bool = False
    ) -> ContextManager[List[Callable[[], None]]]:
        return capture_on_commit_callbacks(using=using, execute=execute)
