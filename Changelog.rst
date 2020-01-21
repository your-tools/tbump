Changelog
=========

v6.0.3 (2020-01-23)
-------------------

* Fix `#44`: when running `tbump init`, do not fail if no files are found matching the current version.

v6.0.2 (2019-07-19)
-------------------

* Implement `#36 <https://github.com/TankerHQ/tbump/issues/36>`_: The ``--only-patch`` flag now allows skipping any git operations or hook commands.

v6.0.1 (2019-07-16)
-------------------

* Fix `#41 <https://github.com/TankerHQ/tbump/issues/41>`_: When run with ``--dry-run``, don't abort if git state is incorrect, just print the error message at the end.

v6.0.0 (2019-07-15)
-------------------

* **Breaking change**: Search strings are now regular expressions
* **Breaking change**: Allow globs in paths (breaking if paths contained ``*``, ``?``, ``[`` or ``]`` characters).

v5.0.4 (2019-03-13)
-------------------
* Preserve line endings when patching files.

v5.0.3 (2018-12-18)
-------------------

* Use new and shiny `cli-ui <https://pypi.org/project/cli-ui/>`_ package instead of old `python-cli-ui`

v5.0.2 (2018-10-11)
-------------------

* Rename ``before_push`` section to ``before_commit``: it better reflets at which
  moment the hook runs. Note that you can still use ``before_push`` or even ``hook`` if
  you want.

v5.0.1 (2018-10-11)
-------------------

* Expose ``tbump.bump_files()`` convenience function.


v5.0.0 (2018-08-27)
-------------------

* **Breaking change**: tbump can now run hooks *after* the push is made. Thus
  ``[[hook]]`` sections should be renamed to ``[before_push]]``  or
  ``[[after_push]]``:

.. code-block:: ini

  # Before (< 5.0.0), running before commit by default:
  [[hook]]
  name = "some hook"
  cmd = "some command"

  # After (>= 5.00), more explicit syntax:
  [[before_push]]
  name = "some hook"
  cmd = "some command"

  # New feature: running after push is made:
  [[after_push]]
  name = "some other hook"
  cmd = "some other command"

* ``tbump init`` now takes the current version directly on the command line instead of interactively asking for it


v4.0.0 (2018-07-13)
-------------------

* Re-add ``--dry-run``
* Add ``tbump init`` to interactively create the ``tbump.toml`` configuration file

v3.0.1 (2018-07-12)
-------------------

* Bug fix: make sure to push the tag *after* the branch. See `#20 <https://github.com/TankerHQ/tbump/issues/20>`_ for the details.

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


* Use annotated tags instead of lightweight tags. Patch by @tux3. See `PR #7 <https://github.com/TankerHQ/tbump/pull/7>`_ for the rationale.
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
