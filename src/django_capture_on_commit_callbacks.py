from unittest import mock

from django.db import DEFAULT_DB_ALIAS, connections


class capture_on_commit_callbacks:
    def __init__(self, *, using=DEFAULT_DB_ALIAS, execute=False):
        self.using = using
        self.execute = execute
        self.callbacks = None

    def __enter__(self):
        if self.callbacks is not None:
            raise RuntimeError("Cannot re-enter capture_on_commit_callbacks()")
        self.callbacks = []
        connection = connections[self.using]
        orig_on_commit = connection.on_commit

        def on_commit_wrapper(func):
            self.callbacks.append(func)
            return orig_on_commit(func)

        self.patcher = mock.patch.object(connection, "on_commit", on_commit_wrapper)
        self.patcher.start()
        return self.callbacks

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.patcher.stop()
        if exc_type is None and self.execute:
            for hook in self.callbacks:
                hook()


class TestCaseMixin:
    @classmethod
    def captureOnCommitCallbacks(cls, *, using=DEFAULT_DB_ALIAS, execute=False):
        return capture_on_commit_callbacks(using=using, execute=execute)
