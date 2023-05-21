Changelog
=========

6.10.0 (2023-05-21)
------------------

Bug fixes:
++++++++++

* Fix #156, where the ``pyproject.toml`` file could not be parsed - patch by @vipcxj
* Fix #158 : also display changes when setting the current version in
  the ``pyproject.toml`` or ``tbump.toml`` files

Other
+++++

* Bump some dependencies
* Add ``--tag-message`` command line option to specify a custom tag message
  (by default it's the same as the tag name) - Patch by Michael Boulton
* Add support for Python 3.11

6.9.0 (2022-03-27)
------------------

* Add ``tbump current-version`` command, to print the current version.
  Path by @blink1073

6.8.0 (2022-03-27)
------------------

* Allow usage of ``python -m tbump`` in addtion to just ``tbump``

6.7.0 (2021-12-22)
------------------

* Drop support for Python 3.6
* Drop dependency on ``attr``

6.6.1 (2021-12-17)
------------------

* Relax dependency on `cli-ui`
* Use a better example in the README (patch by @umonoca)

6.6.0 (2021-11-11)
------------------

Add support for other config paths
++++++++++++++++++++++++++++++++++

Added ``-c, --config`` to ``tbump`` command line, allowing using
a different config file than `tbump.toml` (based on early work by
@achary)

Add support default values for versions fields
++++++++++++++++++++++++++++++++++++++++++++++

Added new ``[[field]]`` option for setting default values for version fields
with no match in the version regex (e.g. prerelease fields),
avoiding errors when these fields are present in a version_template.
Patch by @minrk.

For example:

.. code-block:: toml

   [[field]]
   name = "prerelease"
   default = ""

Other
+++++

* Relax dependency on `attrs` - we used to have ``attrs <20, >=19``, now we have ``attrs >= 20``.

6.5.0 (2021-10-16)
------------------

Instead of pushing twice, which spawns two workflows, ``tbump`` now runs
``git push --atomic <remote> <branch> <tag>``. Patch by @InCogNiTo124.

6.4.1 (2021-10-05)
-------------------

Add support for Python 3.10

6.4.0 (2021-09-14)
-------------------

Breaking change
+++++++++++++++

If you are using `tbump` with a `pyproject.toml` to bump a project using `poetry`,
you may have found that the `version` key in `[tool.poetry]` was implicitly bumped.

This was considered to be a bug, which means you now have to tell `tbump` about `poetry` explicitly:

.. code-block:: toml

   # new
   [[tool.tbump.file]]
   src = "pyproject.toml"
   search = 'version = "{current_version}"'

Bug fixes
+++++++++

* Fix #103: Invalid config: Key 'file' error using pyproject.toml,
  caused by an update in `tomlkit`
* Fix #93: Do not patch version in `[tool.poetry]` implicitly

Misc
++++

* Default development branch is now called `main`.
* Make all `tbump` imports consistent
* Fix compatibly with Python 3.10

6.3.2 (2021-04-19)
------------------

* Move out of the TankerHQ organization
* Fix bug in ``tbump init --pyproject``
* Allow usage of newer ``tomlkit`` versions

6.3.1 (2021-02-05)
------------------

* Add a ``--no-tag-push`` option to create the tag but not push it

6.3.0 (2021-02-05)
------------------

More flexible workflow
+++++++++++++++++++++++

* Add a ``--no-push`` option to create the commit and the tag, but not push them
* Add a ``--no-tag`` option to skip creating the tag

Note that if you want to create a commit and run the hooks but nothing else, you
must use ``tbump --no-tag --no-push <new version>``.

If you only want to patch the files use ``tbump --only-patch``.

See `#65 <https://github.com/dmerejkowsky/tbump/issues/65>`_ for more details

pyproject.toml support
++++++++++++++++++++++

Idea and initial implementation by @pmav99

* If no ``tbump.toml`` file is present, but a ``pyproject.toml`` file
  containing a ``tool.tbump`` section exists, read the configuration from
  there.

* ``tbump init``: add a ``--pyproject`` option to append configuration into
  an existing ``pyproject.toml`` instead of generating the ``tbump.toml`` file

Bug fixes
+++++++++

*  Fix invalid syntax in generated config file (`#80 <https://github.com/dmerejkowsky/tbump/pull/80>`_). Patch by `@snadorp`.

v6.2.0 (2020-11-24)
-------------------

* Drop dependency on ``Path Pie``
* Drop support for Python 3.5, add support for Python 3.9

v6.1.1 (2020-07-23)
-------------------

* Mark this project as typed

v6.1.0 (2020-06-15)
-------------------

* If ``github_url`` is found in the config file, display
  a link suggesting to create a release on GitHub after
  the tag is pushed

v6.0.7 (2020-01-28)
-------------------

* Relax constraint on `path` version

v6.0.6 (2020-01-28)
-------------------

* Switch to `poetry <https://python-poetry.org/>`_ for dependencies management and packaging.

v6.0.5 (2020-01-28)
-------------------

* Fix incorrect `python_requires` metadata
* Fix incorrect `entry_points` metadata

v6.0.3 (2020-01-23)
-------------------

* Fix `#44`: when running `tbump init`, do not fail if no files are found matching the current version.

v6.0.2 (2019-07-19)
-------------------

* Implement `#36 <https://github.com/dmerejkowsky/tbump/issues/36>`_: The ``--only-patch`` flag now allows skipping any git operations or hook commands.

v6.0.1 (2019-07-16)
-------------------

* Fix `#41 <https://github.com/dmerejkowsky/tbump/issues/41>`_: When run with ``--dry-run``, don't abort if git state is incorrect, just print the error message at the end.

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

* Rename ``before_push`` section to ``before_commit``: it better reflects at which
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

* Bug fix: make sure to push the tag *after* the branch. See `#20 <https://github.com/dmerejkowsky/tbump/issues/20>`_ for the details.

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


* Use annotated tags instead of lightweight tags. Patch by @tux3. See `PR #7 <https://github.com/dmerejkowsky/tbump/pull/7>`_ for the rationale.
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
