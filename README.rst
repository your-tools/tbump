tbump: bump software releases
=============================

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
