Changelog
=========

v3.0.1
-------

* Bug fix: make sure to push the tag *after* the branch. See `#20 <https://github.com/SuperTanker/tbump/issues/20>`_ for the details.

v3.0.0 (2018-05-14)
--------------------

* New feature: you can now specify commands to be run after files have been patched and right before git commands are executed.

.. code-block:: ini

      [[hook]]
      name = "Update Cargo.lock"
      cmd = "cargo check"


v2.0.0 (2018-04-26)
-------------------

* Dry run behavior is now activated by default. We start by computing all the changes and then ask if they look good before doing anything. This also means we no
  longer need to pause right before calling ``git push``. Consequently, the ``--dry-run`` option is gone.

* Fix inconsistency: 'current version' was sometimes called 'old version'.

v1.0.2 (2018-04-09)
-------------------

* Fix printing a big ugly stacktrace when looking for the old version number failed for one or more files.

v1.0.1 (2018-04-05)
-------------------


* Use annotated tags instead of lightweight tags. Patch by @tux3. See `PR #7 <https://github.com/SuperTanker/tbump/pull/7>`_ for the rationale.
* When the current branch does not track anything, ask if we should proceed with file replacements and automatic commit and tag (but do not push) instead of aborting immediately.

v1.0.0 (2018-01-16)
-------------------


* First stable release.

Since we use `semver <https://semver.org>`_ this means tbump is now considered stable.

Enjoy!

v0.0.9 (2018-01-13)
-------------------


* Fix regression when using the same file twice

v0.0.8 (2018-01-05)
-------------------

* Allow replacing different types of version. For instance, you may want to write ``pub_version="1.42"`` in one file and ``full_version="1.2.42-rc1"`` in an other.
* Add ``--dry-run`` command line argument
* Improve error handling
* Validate git commit message template
* Validate that current version matches expected regex
* Make sure new version matches the expected regex
* Make sure that custom version templates only contain known groups
* Avoid leaving the repo in an inconsistent state if no match is found
