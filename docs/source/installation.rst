Installation
============

Requirements
------------

* Python 3.12 or higher
* `uv <https://github.com/astral-sh/uv>`_ (recommended) or pip

PyPI Release
------------

.. note::
   Once stable, this package will be officially released and distributed through 
   `PyPI <https://pypi.org/>`_. Stay tuned for updates!

Local Development Installation
------------------------------

For now, you can install the package locally for development:

Using uv (Recommended)
~~~~~~~~~~~~~~~~~~~~~~

`uv <https://github.com/astral-sh/uv>`_ is a fast Python package installer and resolver.

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/DataArtifex/mtnards-toolkit.git
   cd mtnards-toolkit

   # Sync dependencies and install package in editable mode
   uv sync

   # Activate the virtual environment
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate  # On Windows

Using pip
~~~~~~~~~

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/DataArtifex/mtnards-toolkit.git
   cd mtnards-toolkit

   # Create a virtual environment (recommended)
   python -m venv .venv
   source .venv/bin/activate  # On macOS/Linux

   # Install in editable mode
   pip install -e .

Optional Dependencies
---------------------

MCP Server (Separate Package)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MCP server support has moved to a separate package and is not installed with
this toolkit. See the project README for updates on MCP availability.

Development Tools
~~~~~~~~~~~~~~~~~

To install development dependencies (testing, linting, etc.):

.. code-block:: bash

   # With pip
   pip install -e ".[dev]"

   # With uv
   uv sync --all-extras

Documentation Build Tools
~~~~~~~~~~~~~~~~~~~~~~~~~

To build the documentation locally:

.. code-block:: bash

   # With pip
   pip install -e ".[docs]"

   # With uv
   uv sync --group docs

Verification
------------

After installation, verify that the package is correctly installed:

.. code-block:: python

   import dartfx.mtnards
   print(dartfx.mtnards.__version__)

You can also test the basic functionality:

.. code-block:: python

   from dartfx.mtnards import MtnaRdsServer
   
   # Connect to a public server
   server = MtnaRdsServer(host="rds.highvaluedata.net")
   print(server.info)

Configuration
-------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

For production use or when working with authenticated servers, set your credentials 
via environment variables:

.. code-block:: bash

   export MTNA_RDS_HOST="rds.highvaluedata.net"
   export MTNA_RDS_API_KEY="your-api-key"

You can also use a ``.env`` file in your project root:

.. code-block:: text

   MTNA_RDS_HOST=rds.highvaluedata.net
   MTNA_RDS_API_KEY=your-api-key

.. warning::
   Never commit your ``.env`` file to version control. Make sure it's included 
   in your ``.gitignore``.

Troubleshooting
---------------

Import Errors
~~~~~~~~~~~~~

If you encounter import errors, ensure that:

1. You've activated the correct virtual environment
2. The package is installed in editable mode with ``pip install -e .`` or ``uv sync``
3. Your Python version is 3.12 or higher

SSL Certificate Issues
~~~~~~~~~~~~~~~~~~~~~~

If you encounter SSL certificate verification issues when connecting to an RDS server, 
you can temporarily disable SSL verification (not recommended for production):

.. code-block:: python

   server = MtnaRdsServer(
       host="rds.example.com",
       ssl_verify=False  # Use with caution
   )

Next Steps
----------

After installation, proceed to the :doc:`quickstart` guide to learn how to use the toolkit.
