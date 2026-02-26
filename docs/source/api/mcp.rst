MCP API Reference
=================

This page documents the Model Context Protocol (MCP) server implementation.

Overview
--------

The MCP module provides an MCP server that exposes MTNA RDS functionality to AI assistants 
like Claude. It uses the `FastMCP <https://github.com/jlowin/fastmcp>`_ framework.

Server Module
-------------

The server is implemented in ``dartfx.mtnards.mcp.server`` and can be run as:

.. code-block:: bash

   python -m dartfx.mtnards.mcp.server

Server Configuration
--------------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

The server reads these environment variables:

* ``MTNA_RDS_HOST`` - RDS server hostname (default: ``rds.highvaluedata.net``)
* ``MTNA_RDS_API_KEY`` - API key for authentication (optional)

Example:

.. code-block:: bash

   export MTNA_RDS_HOST="rds.example.com"
   export MTNA_RDS_API_KEY="your-api-key"
   python -m dartfx.mtnards.mcp.server

MCP Tools
---------

add
~~~

**Purpose**: Demonstration tool - adds two numbers

**Parameters**:
  * ``a`` (int): First number
  * ``b`` (int): Second number

**Returns**: int - Sum of a and b

.. code-block:: python

   # Implementation
   @mcp.tool()
   def add(a: int, b: int) -> int:
       """Add two numbers"""
       return a + b

MCP Resources
-------------

mtnards://catalog
~~~~~~~~~~~~~~~~~

**Purpose**: Retrieves all catalogs and their data products

**Returns**: list - Catalog information with nested data products

**Structure**:

.. code-block:: python

   [
       {
           "uri": "https://...",
           "id": "catalog_id",
           "name": "Catalog Name",
           "description": "Description",
           "data_products": [
               {
                   "uri": "https://...",
                   "id": "product_id",
                   "name": "Product Name",
                   "description": "Description"
               },
               ...
           ]
       },
       ...
   ]

greeting://{name}
~~~~~~~~~~~~~~~~~

**Purpose**: Example dynamic resource - returns a personalized greeting

**Parameters**:
  * ``name`` (str): Name to greet

**Returns**: str - Greeting message

**Example**: ``greeting://Alice`` returns ``"Hello, Alice!"``

Client Modules
--------------

The toolkit includes example MCP clients for testing:

SSE Client
~~~~~~~~~~

Server-Sent Events client:

.. code-block:: bash

   python -m dartfx.mtnards.mcp.client_sse

STDIO Client
~~~~~~~~~~~~

Standard I/O client:

.. code-block:: bash

   python -m dartfx.mtnards.mcp.client_stdio

Demo Script
~~~~~~~~~~~

Interactive demo:

.. code-block:: bash

   python -m dartfx.mtnards.mcp.demo

Extending the Server
--------------------

Adding New Tools
~~~~~~~~~~~~~~~~

To add a new tool, decorate a function with ``@mcp.tool()``:

.. code-block:: python

   @mcp.tool()
   def get_variable_info(catalog_id: str, product_id: str, variable_id: str) -> dict:
       """Get detailed information about a specific variable.
       
       Args:
           catalog_id: ID of the catalog
           product_id: ID of the data product
           variable_id: ID of the variable
           
       Returns:
           Dictionary with variable details
       """
       catalog = rds_server.catalogs[catalog_id]
       product = catalog.data_products_by_id[product_id]
       variable = product.variables[variable_id]
       
       return {
           "id": variable_id,
           "name": variable.name,
           "label": variable.label,
           "type": variable.data_type,
           "description": variable.description
       }

Adding New Resources
~~~~~~~~~~~~~~~~~~~~

To add a new resource, decorate a function with ``@mcp.resource()``:

.. code-block:: python

   @mcp.resource("mtnards://catalog/{catalog_id}")
   def get_catalog_info(catalog_id: str) -> dict:
       """Get detailed information about a specific catalog.
       
       Args:
           catalog_id: ID of the catalog
           
       Returns:
           Dictionary with catalog details
       """
       catalog = rds_server.catalogs[catalog_id]
       
       return {
           "uri": catalog.uri,
           "id": catalog.id,
           "name": catalog.name,
           "description": catalog.description,
           "product_count": len(catalog.data_products)
       }

Error Handling
--------------

The server includes built-in error handling:

.. code-block:: python

   try:
       mcp.run()
   except Exception as e:
       print(f"Error: {e}", file=sys.stderr)
       sys.exit(1)

For custom error handling in tools:

.. code-block:: python

   @mcp.tool()
   def safe_tool(param: str) -> str:
       """Tool with error handling"""
       try:
           # Implementation
           return result
       except KeyError:
           return "Resource not found"
       except Exception as e:
           logging.error(f"Tool error: {e}")
           return f"Error: {str(e)}"

Logging
-------

The server uses Python's logging module:

.. code-block:: python

   import logging
   import sys

   logging.basicConfig(
       level=logging.DEBUG,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       stream=sys.stderr
   )
   logger = logging.getLogger(__name__)

Logs are written to stderr and can be captured by the MCP client.

Testing
-------

Unit Testing
~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from dartfx.mtnards.mcp import server
   
   def test_server_initialization():
       """Test that server initializes correctly"""
       assert server.rds_server is not None
       assert server.rds_server.host
   
   def test_add_tool():
       """Test the add tool"""
       result = server.add(2, 3)
       assert result == 5

Integration Testing
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Start server in background
   python -m dartfx.mtnards.mcp.server &
   SERVER_PID=$!
   
   # Run tests
   python -m pytest tests/test_mcp.py
   
   # Cleanup
   kill $SERVER_PID

Debugging
---------

Enable debug logging:

.. code-block:: python

   import logging
   logging.basicConfig(level=logging.DEBUG)

Monitor MCP communication:

.. code-block:: bash

   # On macOS
   tail -f ~/Library/Logs/Claude/mcp*.log

Performance Monitoring
----------------------

Track tool execution time:

.. code-block:: python

   import time
   
   @mcp.tool()
   def monitored_tool(param: str) -> str:
       """Tool with performance monitoring"""
       start = time.time()
       
       # Implementation
       result = perform_operation(param)
       
       elapsed = time.time() - start
       logging.info(f"Tool executed in {elapsed:.3f}s")
       
       return result

Best Practices
--------------

1. **Type Hints**: Always include type hints for parameters and return values
2. **Documentation**: Write clear docstrings for all tools and resources
3. **Error Handling**: Implement proper error handling and logging
4. **Validation**: Validate input parameters before processing
5. **Caching**: Cache expensive operations when appropriate
6. **Testing**: Write tests for all custom tools and resources

Related Resources
-----------------

* `Model Context Protocol Specification <https://modelcontextprotocol.io/>`_
* `FastMCP Documentation <https://github.com/jlowin/fastmcp>`_
* `Claude MCP Integration Guide <https://docs.anthropic.com/claude/docs/mcp>`_
* :doc:`../mcp_server` - User guide for MCP server setup
