tbump: bump software releases
=============================


.. image:: https://img.shields.io/travis/SuperTanker/tbump.svg?branch=master
  :target: https://travis-ci.org/SuperTanker/tbump

.. image:: https://img.shields.io/pypi/v/tbump.svg
  :target: https://pypi.org/project/tbump/

.. image:: https://img.shields.io/github/license/SuperTanker/tbump.svg
  :target: https://github.com/SuperTanker/tbump/blob/master/LICENSE


Installation
------------

* Make sure you are using Python **3.4** or later
* Intall ``tbump`` with ``pip`` as usual.

Screenshot
-----------

Here's what a typical usage of ``tbump`` looks like:

.. image:: https://raw.githubusercontent.com/SuperTanker/tbump/master/scrot.png

Usage
------

Create a ``tbump.toml`` file looking like:

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
 * The version regular expression will be used in `verbose mode <https://docs.python.org/3/library/re.html#re.VERBOSE>`_ and must contain named groups.

Then run:

.. code-block:: console

    $ tbump 1.2.42

``tbump`` will:

* Replace the string ``1.2.41`` by ``1.2.42`` in every file listed in the
  configuration

* Make a commit based on the ``message_template``.

* Make an **annotated** tag based on the ``tag_template``

* Ask wether to push the current branch and the tag (unless ``--no-interactive`` is used)


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
