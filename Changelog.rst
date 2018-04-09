Changelog
=========

v1.0.2
------

* Fix printing a big ugly stacktrace when the looking for the old version number failed for one or more files.

v1.0.1
------


* Use annotated tags instead of lightweight tags. Patch by @tux3. See `PR #7 <https://github.com/SuperTanker/tbump/pull/7>`_ for the rationale.
* When the current branch does not track anything, ask if we should proceed with file replacements and automatic commit and tag (but do not push) instead of aborting immediately.

v1.0.0
-------


* First stable release.

Since we use `semver <https://semver.org>`_ this means tbump is now considered stable.

Enjoy!

v0.0.9
------


* Fix regression when using the same file twice

v0.0.8
--------

* Allow replacing different types of version. For instance, you may want to write ``pub_version="1.42"`` in one file and ``full_version="1.2.42-rc1"`` in an other.
* Add ``--dry-run`` command line argument
* Improve error handling
* Validate git commit message template
* Validate that current version matches expected regex
* Make sure new version matches the expected regex
* Make sure that custom version templates only contain known groups
* Avoid leaving the repo in an inconsistent state if no match is found
