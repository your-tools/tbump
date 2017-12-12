tbump: bump software releases
=============================

.. image:: https://img.shields.io/travis/SuperTanker/tbump.svg?branch=master
  :target: https://travis-ci.org/SuperTanker/tbump

.. image:: https://img.shields.io/github/license/SuperTanker/tbump.svg
  :target: https://github.com/SuperTanker/tbump/blob/master/LICENSE

Installation
------------

* Make sure you are using Python **3.4** or later
* Intall ``tbump`` with ``pip`` as usual.

Usage
------

Create a ``tbump.toml`` file looking like:

.. code-block:: ini

    [version]
    current = "1.2.41"

    [git]
    message_template = "Bump to {new_version}"
    tag_template = "v{new_version}"

    [[file]]
    src = "setup.py"


Then run:

.. code-block:: console

    $ tbump 1.2.42

``tbump`` will:

* Replace the string ``1.2.41`` by ``1.2.42`` in every file listed in the
  configuration

* Make a commit based on the ``message_template``

* Make a tag based on the ``tag_template``

* Ask wether to push the current branch and the tag (unless ``--no-interactive`` is used)


Screenshot
-----------

Here's what a typical usage of ``tbump`` looks like:

.. image:: https://raw.githubusercontent.com/SuperTanker/tbump/master/scrot.png
