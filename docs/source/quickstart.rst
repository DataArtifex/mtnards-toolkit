Quick Start Guide
=================

This guide will walk you through the basics of using the MTNA RDS Toolkit.

Prerequisites
-------------

Make sure you have installed the toolkit. See :doc:`installation` for details.

Basic Workflow
--------------

The typical workflow involves three main steps:

1. Connect to an RDS server
2. Browse catalogs and data products
3. Work with data product metadata and variables

Step 1: Connect to an RDS Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, create a connection to an MTNA RDS server:

.. code-block:: python

   from dartfx.mtnards import MtnaRdsServer

   # Connect to the High-Value Data Network (public server)
   server = MtnaRdsServer(host="rds.highvaluedata.net")

   # View server information
   print(server.info.name)
   print(server.info.version)

For servers requiring authentication:

.. code-block:: python

   server = MtnaRdsServer(
       host="rds.example.com",
       api_key="your-api-key-here"
   )

Or using environment variables:

.. code-block:: python

   import os

   server = MtnaRdsServer(
       host=os.getenv("MTNA_RDS_HOST"),
       api_key=os.getenv("MTNA_RDS_API_KEY")
   )

Step 2: Browse Catalogs
~~~~~~~~~~~~~~~~~~~~~~~

Explore the available catalogs on the server:

.. code-block:: python

   # List all catalogs
   for catalog_id, catalog in server.catalogs.items():
       print(f"ID: {catalog_id}")
       print(f"Name: {catalog.name}")
       print(f"Description: {catalog.description}")
       print("---")

   # Access a specific catalog
   anes_catalog = server.catalogs['us-anes']
   print(f"Catalog: {anes_catalog.name}")

Step 3: Explore Data Products
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Browse data products (datasets) within a catalog:

.. code-block:: python

   # List all data products in a catalog
   for data_product in anes_catalog.data_products:
       print(f"ID: {data_product.id}")
       print(f"Name: {data_product.name}")
       print("---")

   # Access a specific data product by ID
   anes_1948 = anes_catalog.data_products_by_id['anes_1948']
   print(f"Dataset: {anes_1948.name}")
   print(f"Description: {anes_1948.description}")

Step 4: Work with Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Examine the variables (fields/columns) in a data product:

.. code-block:: python

   # List all variables
   for var_id, variable in anes_1948.variables.items():
       print(f"Variable ID: {var_id}")
       print(f"Name: {variable.name}")
       print(f"Label: {variable.label}")
       print(f"Type: {variable.data_type}")
       print("---")

   # Access a specific variable
   var = anes_1948.variables['V480018']
   print(f"Variable: {var.label}")
   print(f"Description: {var.description}")

Working with Classifications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For categorical variables, you can access their classification codes:

.. code-block:: python

   # Check if a variable has classifications
   if var.classification_stub:
       classification = var.classification
       print(f"Classification: {classification.name}")

       # List classification codes
       for code in classification.codes.values():
           print(f"{code.value}: {code.label}")

Common Use Cases
----------------

Generate Croissant Metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create ML-ready dataset documentation in Croissant format:

.. code-block:: python

   # Generate Croissant metadata for a data product
   croissant_metadata = anes_1948.croissant()

   # Save to file
   with open('anes_1948.croissant.jsonld', 'w') as f:
       f.write(croissant_metadata.to_json())

   # Or get as dictionary
   metadata_dict = croissant_metadata.metadata.to_json()

Export DCAT/RDF
~~~~~~~~~~~~~~~

Generate semantic web metadata in DCAT format:

.. code-block:: python

   from dartfx.mtnards.dcat import MtnaRdsDcat

   # Create DCAT exporter
   dcat = MtnaRdsDcat(
       server=server,
       catalog=anes_catalog,
       data_product=anes_1948,
       uri_style="uuid"  # Options: "uuid", "uuid_urn", "hostname"
   )

   # Generate RDF graph
   graph = dcat.graph()

   # Export as Turtle
   turtle = graph.serialize(format='turtle')
   print(turtle)

   # Or save to file
   with open('anes_1948.ttl', 'w') as f:
       f.write(turtle)

Generate Markdown Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create human-readable documentation for a dataset:

.. code-block:: python

   # Generate markdown documentation
   markdown = anes_1948.markdown()

   # Save to file
   with open('anes_1948.md', 'w') as f:
       f.write(markdown)

Complete Example
----------------

Here's a complete example that ties everything together:

.. code-block:: python

   import os
   from dartfx.mtnards import MtnaRdsServer
   from dartfx.mtnards.dcat import MtnaRdsDcat

   # 1. Connect to server
   server = MtnaRdsServer(host="rds.highvaluedata.net")
   print(f"Connected to: {server.info.name}")

   # 2. Get a catalog
   catalog = server.catalogs['us-anes']
   print(f"Working with catalog: {catalog.name}")

   # 3. Get a data product
   data_product = catalog.data_products_by_id['anes_1948']
   print(f"Dataset: {data_product.name}")
   print(f"Variables: {len(data_product.variables)}")

   # 4. Generate metadata in multiple formats

   # Croissant for ML
   croissant = data_product.croissant()
   with open('output.croissant.jsonld', 'w') as f:
       f.write(croissant.to_json())
   print("✓ Croissant metadata generated")

   # DCAT for semantic web
   dcat = MtnaRdsDcat(
       server=server,
       catalog=catalog,
       data_product=data_product
   )
   with open('output.ttl', 'w') as f:
       f.write(dcat.graph().serialize(format='turtle'))
   print("✓ DCAT/RDF metadata generated")

   # Markdown documentation
   with open('output.md', 'w') as f:
       f.write(data_product.markdown())
   print("✓ Markdown documentation generated")

   print("\nAll metadata files generated successfully!")

Interactive Shell CLI
---------------------

The MTNA RDS Toolkit includes a powerful interactive shell for hands-on metadata exploration.

Step 1: Start the Shell
~~~~~~~~~~~~~~~~~~~~~~~

Launch the interactive shell directly from your terminal:

.. code-block:: bash

   dartfx-mtnards

You can also start the shell directly focused on a specific path:

.. code-block:: bash

   dartfx-mtnards --path us-anes/anes1948

Step 2: Navigate and Explore
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use familiar hierarchical commands to browse catalogs and products:

.. code-block:: text

   # List catalogs
   ls

   # Navigate into a catalog (supports absolute / paths)
   cd /us-anes

   # List data products
   ls

   # Navigate into a specific dataset
   cd anes1948

   # List variables (displays statistical roles and code counts)
   vars

Step 3: Inspect Metadata
~~~~~~~~~~~~~~~~~~~~~~~~

View detailed properties and classification codes:

.. code-block:: text

   # Show dataset metadata
   show .

   # Show a specific variable and its first 10 classification codes
   show VVERSION --codes

   # Use command aliases for efficiency
   cls

Step 4: Monitor API Performance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Audit the precise timing and status of underlying RDS API calls:

.. code-block:: text

   api

Error Handling
--------------

Always handle potential errors when working with remote servers:

.. code-block:: python

   try:
       server = MtnaRdsServer(host="rds.highvaluedata.net")
       catalogs = server.catalogs
   except Exception as e:
       print(f"Error connecting to server: {e}")

.. code-block:: python

   # Check if a catalog exists before accessing
   if 'us-anes' in server.catalogs:
       catalog = server.catalogs['us-anes']
   else:
       print("Catalog not found")

Next Steps
----------

* Explore more detailed :doc:`examples`
* Read the :doc:`api/core` reference
* Check out the `GitHub repository <https://github.com/DataArtifex/mtnards-toolkit>`_ for more examples
