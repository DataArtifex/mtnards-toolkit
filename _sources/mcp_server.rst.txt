MCP Server Integration
======================

The MTNA RDS Toolkit includes a Model Context Protocol (MCP) server that enables AI assistants 
like Claude to interact directly with MTNA RDS servers.

What is MCP?
------------

`Model Context Protocol (MCP) <https://modelcontextprotocol.io/>`_ is an open protocol that 
standardizes how AI applications interact with external data sources and tools. The MTNA RDS 
MCP server exposes the toolkit's functionality as MCP tools and resources, allowing AI assistants 
to discover datasets, retrieve metadata, and help construct queries.

Installation
------------

The MCP server requires additional dependencies:

.. code-block:: bash

   pip install -e ".[mcp]"

Or with uv:

.. code-block:: bash

   uv sync  # MCP dependencies are included by default

Running the Server
------------------

Standalone Mode
~~~~~~~~~~~~~~~

Run the MCP server directly:

.. code-block:: bash

   python -m dartfx.mtnards.mcp.server

With environment variables:

.. code-block:: bash

   export MTNA_RDS_HOST="rds.highvaluedata.net"
   export MTNA_RDS_API_KEY="your-api-key"
   python -m dartfx.mtnards.mcp.server

Claude Desktop Integration
---------------------------

To integrate with Claude Desktop, add the server to your Claude configuration file.

Configuration Location
~~~~~~~~~~~~~~~~~~~~~~

* **macOS**: ``~/Library/Application Support/Claude/claude_desktop_config.json``
* **Windows**: ``%APPDATA%\Claude\claude_desktop_config.json``
* **Linux**: ``~/.config/Claude/claude_desktop_config.json``

Configuration Example
~~~~~~~~~~~~~~~~~~~~~

Add the following to your ``claude_desktop_config.json``:

.. code-block:: json

   {
     "mcpServers": {
       "mtnards": {
         "command": "uv",
         "args": [
           "--directory",
           "/path/to/mtnards-toolkit",
           "run",
           "python",
           "-m",
           "dartfx.mtnards.mcp.server"
         ],
         "env": {
           "MTNA_RDS_HOST": "rds.highvaluedata.net",
           "MTNA_RDS_API_KEY": "your-api-key"
         }
       }
     }
   }

Replace ``/path/to/mtnards-toolkit`` with the actual path to your installation.

Using with pip/venv
~~~~~~~~~~~~~~~~~~~

If you're not using uv, configure with Python directly:

.. code-block:: json

   {
     "mcpServers": {
       "mtnards": {
         "command": "python",
         "args": [
           "-m",
           "dartfx.mtnards.mcp.server"
         ],
         "env": {
           "MTNA_RDS_HOST": "rds.highvaluedata.net",
           "PYTHON_PATH": "/path/to/mtnards-toolkit/src"
         }
       }
     }
   }

Available MCP Tools
-------------------

Once configured, Claude can use these tools:

get_server_catalogs
~~~~~~~~~~~~~~~~~~~

Retrieves all catalogs available on the server along with their data products.

**Response includes:**

* Catalog URI, ID, name, and description
* List of data products in each catalog
* Data product URIs, IDs, names, and descriptions

Example Claude interaction:

   **User**: "What catalogs are available on the RDS server?"
   
   **Claude**: Uses ``get_server_catalogs`` tool and displays the results.

Future Tools (Coming Soon)
---------------------------

The following tools are planned for future releases:

* ``get_catalog`` - Retrieve detailed catalog information
* ``get_catalog_metadata`` - Get all classifications and variables in a catalog
* ``get_data_product`` - Retrieve specific data product details
* ``get_data_product_variables`` - List all variables in a data product
* ``query_data`` - Execute queries to subset and aggregate data

MCP Resources
-------------

The server exposes resources that can be accessed by MCP clients:

mtnards://catalog
~~~~~~~~~~~~~~~~~

Returns the complete catalog structure including all data products.

greeting://{name}
~~~~~~~~~~~~~~~~~

Example resource for testing - returns a personalized greeting.

Using the MCP Server with Claude
---------------------------------

Example Interactions
~~~~~~~~~~~~~~~~~~~~

Once configured, you can ask Claude questions like:

* "What datasets are available on the MTNA RDS server?"
* "Show me the catalogs and their data products"
* "What information do you have about the US ANES catalog?"
* "List the data products in the us_anes catalog"

Claude will automatically use the MCP server tools to retrieve and present the information.

Example Session
~~~~~~~~~~~~~~~

.. code-block:: text

   User: What datasets are available on the RDS server?
   
   Claude: I'll check the available catalogs and datasets.
   
   [Claude uses get_server_catalogs tool]
   
   Claude: The server has several catalogs:
   
   1. US ANES (American National Election Studies)
      - Contains 72 data products
      - Includes election studies from 1948-2020
      
   2. US Census
      - Contains demographic and economic data
      - Multiple data products for different census years
   
   [etc...]

Best Practices
--------------

Security
~~~~~~~~

* **Never commit API keys** to version control
* Use environment variables or secure secret management
* Rotate API keys regularly
* Use read-only API keys when possible

Performance
~~~~~~~~~~~

* The MCP server caches catalog and server information
* First requests may be slower while data is fetched
* Subsequent requests use cached data for better performance

Debugging
~~~~~~~~~

Enable debug logging to troubleshoot issues:

.. code-block:: python

   import logging
   logging.basicConfig(level=logging.DEBUG)

Check the server logs (stderr) for detailed information about MCP calls and RDS API requests.

Troubleshooting
---------------

Server Not Starting
~~~~~~~~~~~~~~~~~~~

**Check that:**

1. Python 3.12+ is installed
2. All dependencies are installed (``pip install -e ".[mcp]"``)
3. Environment variables are set correctly
4. The path in ``claude_desktop_config.json`` is correct

**View logs:**

On macOS/Linux:

.. code-block:: bash

   tail -f ~/Library/Logs/Claude/mcp*.log

Claude Can't Connect
~~~~~~~~~~~~~~~~~~~~

1. Restart Claude Desktop after configuration changes
2. Verify the JSON configuration syntax is valid
3. Check that the server path is absolute, not relative
4. Ensure environment variables are set in the config

API Authentication Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~

If you see authentication errors:

1. Verify your API key is correct
2. Check that the API key has the necessary permissions
3. Ensure the ``MTNA_RDS_API_KEY`` environment variable is set in the MCP config

Development
-----------

Running in Development Mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For development, you can run the server with additional debugging:

.. code-block:: bash

   # With logging
   PYTHONPATH=./src python -m dartfx.mtnards.mcp.server 2>&1 | tee mcp.log
   
   # With uv
   uv run python -m dartfx.mtnards.mcp.server

Testing the Server
~~~~~~~~~~~~~~~~~~

Use the included test clients:

.. code-block:: bash

   # SSE client
   python -m dartfx.mtnards.mcp.client_sse
   
   # STDIO client
   python -m dartfx.mtnards.mcp.client_stdio

Extending the Server
~~~~~~~~~~~~~~~~~~~~

To add new MCP tools or resources, edit ``src/dartfx/mtnards/mcp/server.py``:

.. code-block:: python

   @mcp.tool()
   def my_custom_tool(param: str) -> str:
       """Description of what the tool does"""
       # Implementation
       return result
   
   @mcp.resource("mtnards://custom/{id}")
   def get_custom_resource(id: str) -> dict:
       """Description of the resource"""
       # Implementation
       return data

Additional Resources
--------------------

* `Model Context Protocol Documentation <https://modelcontextprotocol.io/>`_
* `FastMCP Documentation <https://github.com/jlowin/fastmcp>`_
* `Claude Desktop MCP Guide <https://docs.anthropic.com/claude/docs/mcp>`_
* `MTNA RDS Toolkit GitHub <https://github.com/DataArtifex/mtnards-toolkit>`_
