.. image:: https://img.shields.io/pypi/v/tbump.svg
  :target: https://pypi.org/project/tbump/

.. image:: https://img.shields.io/github/license/dmerejkowsky/tbump.svg
  :target: https://github.com/dmerejkowsky/tbump/blob/main/LICENSE

.. image:: https://github.com/dmerejkowsky/tbump/workflows/tests/badge.svg
   :target: https://github.com/dmerejkowsky/tbump/actions

.. image:: https://github.com/dmerejkowsky/tbump/workflows/linters/badge.svg
   :target: https://github.com/dmerejkowsky/tbump/actions

.. image:: https://img.shields.io/badge/deps%20scanning-pyup.io-green
   :target: https://github.com/dmerejkowsky/tbump/workflows/safety/

.. image:: https://img.shields.io/badge/code%20style-black-black.svg
   :target: https://github.com/psf/black

.. image:: https://img.shields.io/badge/mypy-checked-blue.svg
   :target: https://mypy-lang.org


tbump: bump software releases
=============================

tbump helps you bump the version of your project in a easy way.

Note
----

This project was originally hosted on the `TankerHQ
<https://github.com/TankerHQ>`_ organization, which was my employer from 2016
to 2021. They kindly agreed to give back ownership of this project to
me. Thanks!

Installation
------------

The recommended way to install ``tbump`` is to use `pipx <https://pipxproject.github.io/pipx/>`_

* Make sure to have Python **3.7** or later installed.
* Install ``pipx``
* Run ``pipx install tbump``.

``tbump`` is also available on ``pypi`` and can be installed with ``pip`` if you know what you are doing.

Screenshot
-----------

Here's what a typical usage of ``tbump`` looks like:

.. code-block:: console

    $ tbump 5.0.5
    :: Bumping from 5.0.4 to 5.0.5
    => Would patch these files
    - setup.py:14 version="5.0.4",
    + setup.py:14 version="5.0.5",
    - tbump.toml:2 current = "5.0.4"
    + tbump.toml:2 current = "5.0.5"
    => Would run these hooks before commit
    * (1/2) $ ./test.sh
    * (2/2) $ grep -q -F 5.0.5 Changelog.rst
    => Would run these git commands
     * git add --update
     * git commit --message Bump to 5.0.5
     * git tag --annotate --message v5.0.5 v5.0.5
     * git push origin master
     * git push origin v5.0.5
    => Would run these hooks after push
    * (1/1) $ ./publish.sh
    :: Looking good? (y/N)
    y
    => Patching files
    ...
    => Running hooks before commit
    ...
    => Making bump commit and push matching tags
    ...
    => Running hooks after push
    ...
    Done ✓



Usage
------

First, run ``tbump init <current_version>``, where ``current_version``
is the current version of your program. This will create a
``tbump.toml`` file looking like this:

.. code-block:: ini

    [version]
    current = "1.2.41"
    regex = '''
      (?P<major>\d+)
      \.
      (?P<minor>\d+)
      \.
      (?P<patch>\d+)
    '''

    [git]
    message_template = "Bump to {new_version}"
    tag_template = "v{new_version}"

    [[file]]
    src = "setup.py"


.. note::

 * The file uses `toml syntax <https://github.com/toml-lang/toml>`_.
 * Strings should be templated using curly brackets, to be used with
   Python's built-in ``.format()`` method.
 * Paths may contain unix-style `globs
   <https://docs.python.org/3/library/glob.html>`_, e.g. ``src =
   "a/**/script.?s"`` matches both ``a/b/script.js`` and
   ``a/b/c/script.ts``.
 * The version regular expression will be used in `verbose mode
   <https://docs.python.org/3/library/re.html#re.VERBOSE>`_ and can
   contain named groups (see below).
 * tbump will also look for a ``[tool.tbump]`` section in the
   `pyproject.toml` file if its exists. You can use ``tbump init`` with
   the ``--pyproject`` option to append the configuration in this file
   instead of creating a new file.


Then run:

.. code-block:: console

    $ tbump 1.2.42

``tbump`` will:

* Replace the string ``1.2.41`` by ``1.2.42`` in every file listed in the
  configuration

* Make a commit based on the ``message_template``.

* Make an **annotated** tag based on the ``tag_template``

* Push the current branch and the tag.

Note that by default, ``tbump`` will display all the changes and stop to ask if they are correct before performing any action, allowing you to abort and re-try the bump if something is not right.
You can use ``--non-interactive`` to disable this behavior.

If you only want to bump the files without performing any git actions or running the hook commands, use the ``--only-patch`` option.

Advanced configuration
----------------------

Restricting the lines that are replaced
+++++++++++++++++++++++++++++++++++++++


Sometimes you want to make sure only the line matching a given pattern is replaced. For instance, with the following ``package.json``:

.. code-block:: js

    /* in package.json */
    {
       "name": "foo",
       "version": "0.42",
       "dependencies": {
         "some-dep": "0.42",
         "other-dep": "1.3",
       }
    }

you'll want to make sure that when you bump from ``0.42`` to ``0.43`` that the line containing ``some-dep`` does not change.

In this case, you can set a ``search`` option in the ``file`` section:

.. code-block:: ini

    # In tbump.toml

    [[file]]
    src = "package.json"
    search = '"version": "{current_version}"'

Note that the search string is actually a full regular expression, except for the ``{current_version}`` marker which is substituted as plain text.


Using a custom version template
+++++++++++++++++++++++++++++++

If you are using a version schema like ``1.2.3-alpha-4``, you may want to expose a variable that only contains the "public" part of the version string. (``1.2.3`` in this case).

To do so, add a ``version_template`` option in the ``file`` section. The names used in the format string should match the group names in the regular expression.


.. code-block:: js

      /* in version.js */

      export FULL_VERSION = '1.2.3-alpha-4';
      export PUBLIC_VERSION = '1.2.3';

.. code-block:: ini


      [[file]]
      src = "version.js"
      version_template = "{major}.{minor}.{patch}"
      search = "export PUBLIC_VERSION = '{current_version}'"

      [[file]]
      src = "version.js"
      search = "export FULL_VERSION = '{current_version}'"


Running commands before commit
++++++++++++++++++++++++++++++

You can specify a list of hooks to be run after the file have changed, but before the commit is made and pushed.

This is useful if some of the files under version control are generated through an external program.

Here's an example:


.. code-block:: ini

    [[before_commit]]
    name = "Check Changelog"
    cmd = "grep -q -F {new_version} Changelog.rst"


The name is mandatory. The command will be executed via the shell, after the  ``{new_version}``  placeholder is replaced with the new version.

Any hook that fails will interrupt the bump. You may want to run ``git reset --hard`` before trying again to undo the changes made in the files.

Running commands after push
+++++++++++++++++++++++++++

You can specify a list of hooks to be run right after the tag has been pushed, using an `[[after_push]]` section.

This is useful if you need the command to run on a clean repository, without un-committed changes, for instance to publish ``rust`` packages:

.. code-block:: ini

    [[after_push]]
    name = "Publish to crates.io"
    cmd = "cargo publish"


Setting default values for version fields
+++++++++++++++++++++++++++++++++++++++++


(Added in 6.6.0)

If you have a ``version_template`` that includes fields that don't always have a match
(e.g. prerelease info),
you can set a default value to use instead of ``None``,
which would raise an error.

For example:

.. code-block:: ini

    [version]
    current = "1.2.3"
    regex = """
      (?P<major>\d+)
      \.
      (?P<minor>\d+)
      \.
      (?P<patch>\d+)
      (\-
        (?P<extra>.+)
      )?
      """

    [[file]]
    src = "version.py"
    version_template = '({major}, {minor}, {patch}, "{extra}")'
    search = "version_info = {current_version}"

    [[field]]
    # the name of the field
    name = "extra"
    # the default value to use, if there is no match
    default = ""
