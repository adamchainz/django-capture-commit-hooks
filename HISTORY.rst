=======
History
=======

* Support Python 3.10.

* Stop distributing tests to reduce package size. Tests are not intended to be
  run outside of the tox setup in the repository. Repackagers can use GitHub's
  tarballs per tag.

1.4.0 (2021-01-25)
------------------

* Support Django 3.2.

1.3.0 (2020-12-13)
------------------

* Drop Python 3.5 support.
* Support Python 3.9.

1.2.0 (2020-05-24)
------------------

* Drop Django 2.0 and 2.1 support.
* Use ``@contextlib.contextmanager``.

1.1.0 (2020-05-24)
------------------

* Made ``captureOnCommitCallbacks()`` a ``classmethod`` so it can be used from within class methods such as ``setUpClass()``, ``setUpTestData()``.
* Avoiding capturing callbacks enqueued within rolled back ``atomic()`` blocks.
  As a side effect of this change, the returned list of callbacks is only populated when the context manager exits.
* Add Django 3.1 support.

1.0.0 (2020-05-20)
------------------

* Initial release.
