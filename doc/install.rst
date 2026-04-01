=====================
 Installation Guide
=====================

as3lib-miniAMF requires Python_ 3.9+, and DefusedXML_.


Easy Installation
=================

The easiest way to install as3lib-miniAMF is with ``pip``::

    pip install as3lib-miniAMF


Manual Installation
===================

First install DefusedXML_.  If you wish to build the C accelerator
module, you will also need a C compiler and the libraries for
compiling Python extensions.

:doc:`download` the as3lib-miniAMF archive of your choice and install it
using ``pip``::

    pip install as3lib-miniamf-<version>.tar.gz

This will byte-compile the Python source code and install it in the
``site-packages`` directory of your Python installation.


Unit Tests
==========

Unit tests for as3lib-miniAMF require uv_. I will not go over installing
uv because it has much better instructions. Once uv is installed, you
need to install tox as a uv tool which can be done using the following
command::

    uv tool install tox --with tox-uv

Once tox is installed, you can run the unit tests by running the following
command from the source directory::

    uv tool run tox


C Accelerator Module
====================

The C accelerator modules are currently not optional.


Documentation
=============

To build the documentation you need Sphinx_.  The `official
documentation`_ is generated with Sphinx 1.5 running under Python 3.5.
Older versions of Sphinx and/or Python may also work.

From the ``doc`` subdirectory of the source distribution, run this
command::

    sphinx-build -b html . _build

This will generate HTML documentation in the ``doc/_build``
folder.

.. _Python:                  https://www.python.org/
.. _DefusedXML:              https://pypi.python.org/pypi/defusedxml
.. _Cython:                  http://cython.org
.. _Sphinx:                  http://www.sphinx-doc.org/
.. _official documentation:  https://mini-amf.readthedocs.io/
