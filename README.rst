tbump: bump software releases
=============================


.. image:: https://img.shields.io/travis/TankerHQ/tbump.svg?branch=master
  :target: https://travis-ci.org/TankerHQ/tbump

.. image:: https://img.shields.io/pypi/v/tbump.svg
  :target: https://pypi.org/project/tbump/
  
.. image:: https://img.shields.io/pypi/pyversions/tbump.svg
  :target: https://pypi.org/project/tbump
  

.. image:: https://img.shields.io/github/license/TankerHQ/tbump.svg
  :target: https://github.com/TankerHQ/tbump/blob/master/LICENSE
  
.. image:: https://img.shields.io/codecov/c/github/TankerHQ/tbump.svg?label=Coverage
   :target: https://codecov.io/gh/TankerHQ/tbump


Installation
------------

* Make sure you are using Python **3.5** or later
* Intall ``tbump`` with ``pip`` as usual.

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
    * (1/2) $ python ci/ci.py
    * (2/2) $ grep -q 5.0.5 Changelog.rst
    => Would run these git commands
     * git add --update
     * git commit --message Bump to 5.0.5
     * git tag --annotate --message v5.0.5 v5.0.5
     * git push origin master
     * git push origin v5.0.5
    => Would run these hooks after push
    * (1/1) $ tools/publish.sh
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

Frist, run ``tbump init``. This will create a ``tbump.toml`` file looking like this:

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
 * Strings should be templated using curly brackets, to be used with Python's built-in ``.format()`` method.
 * Paths may contain unix-style `globs <https://docs.python.org/3/library/glob.html>`_, e.g. ``src = "a/**/script.?s"`` matches both ``a/b/script.js`` and ``a/b/c/script.ts``.
 * The version regular expression will be used in `verbose mode <https://docs.python.org/3/library/re.html#re.VERBOSE>`_ and must contain named groups.

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


Sometimes you want to make sure only the line matching a given pattern is replaced. For instance, with the folliwing ``package.json``:

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

To do so, add a ``version_template`` option in te ``file`` section. The names used in the format string should match the group names in the regular expression.


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
    cmd = "grep -q {new_version} Changelog.rst"


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
