from functools import partial
from unittest import mock

import django
import pytest
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.db.utils import IntegrityError
from django.test import SimpleTestCase, TestCase

from django_capture_on_commit_callbacks import (
    TestCaseMixin,
    capture_on_commit_callbacks,
    check_django_version,
)

mock_django_version = partial(mock.patch.object, django, "VERSION")


class CheckDjangoVersionTests(SimpleTestCase):
    def test_old_django(self):
        with mock_django_version((3, 1)):
            check_django_version()

    def test_new_django(self):
        with mock_django_version((3, 2)), pytest.raises(
            ImproperlyConfigured
        ) as excinfo:
            check_django_version()

        assert len(excinfo.value.args) == 1
        assert excinfo.value.args[0].startswith(
            "django-capture-on-commit-callbacks is unnecessary on Django 3.2+."
        )


if django.VERSION >= (3, 2):
    # Cannot subclass the mixin on Django 3.2+

    class CaptureOnCommitCallbacksTests(TestCase):
        def test_calling_errors(self):
            with pytest.raises(ImproperlyConfigured) as excinfo:
                with capture_on_commit_callbacks():
                    pass

            assert excinfo.value.args[0].startswith(
                "django-capture-on-commit-callbacks is unnecessary on Django 3.2+."
            )

    class TestCaseMixinTests(TestCase):
        def test_subclass_errors(self):
            with pytest.raises(ImproperlyConfigured) as excinfo:

                class TestTestCase(TestCaseMixin, TestCase):
                    pass

            assert excinfo.value.args[0].startswith(
                "django-capture-on-commit-callbacks is unnecessary on Django 3.2+."
            )


else:

    class CaptureOnCommitCallbacksTests(TestCase):  # type: ignore [no-redef]
        databases = ["default", "other"]
        callback_called = False

        def enqueue_callback(self):
            def hook():
                self.callback_called = True

            transaction.on_commit(hook)

        def test_with_no_arguments(self):
            with capture_on_commit_callbacks() as callbacks:
                response = self.client.post(
                    "/contact/",
                    {"message": "I like your site"},
                )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(callbacks), 1)
            # Execute the hook
            callbacks[0]()
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, "Contact Form")
            self.assertEqual(mail.outbox[0].body, "I like your site")

        def test_with_execute(self):
            with capture_on_commit_callbacks(execute=True) as callbacks:
                response = self.client.post(
                    "/contact/",
                    {"message": "I like your site"},
                )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(callbacks), 1)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, "Contact Form")
            self.assertEqual(mail.outbox[0].body, "I like your site")

        def test_with_alternate_database(self):
            with capture_on_commit_callbacks(using="other", execute=True) as callbacks:
                response = self.client.post(
                    "/contact/",
                    {"message": "I like your site", "using": "other"},
                )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(callbacks), 1)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, "Contact Form")
            self.assertEqual(mail.outbox[0].body, "I like your site")

        def test_wih_rolled_back_savepoint(self):
            with capture_on_commit_callbacks() as callbacks:
                try:
                    with transaction.atomic():
                        self.client.post(
                            "/contact/",
                            {"message": "I like your site"},
                        )
                        raise IntegrityError()
                except IntegrityError:
                    # inner transaction.atomic() has been rolled back.
                    pass

            self.assertEqual(callbacks, [])

        def test_execute_recursive(self):
            with capture_on_commit_callbacks(execute=True) as callbacks:
                transaction.on_commit(self.enqueue_callback)

            self.assertEqual(len(callbacks), 2)
            self.assertIs(self.callback_called, True)

    class TestCaseMixinTests(TestCaseMixin, TestCase):  # type: ignore [no-redef]
        databases = ["default", "other"]

        def test_with_execute(self):
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                response = self.client.post(
                    "/contact/",
                    {"message": "I like your site"},
                )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(callbacks), 1)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, "Contact Form")
            self.assertEqual(mail.outbox[0].body, "I like your site")
