Examples
========

This page provides detailed examples for common use cases of the MTNA RDS Toolkit.

Working with Multiple Catalogs
-------------------------------

Iterate through all catalogs and their data products:

.. code-block:: python

   from dartfx.mtnards import MtnaRdsServer
   
   server = MtnaRdsServer(host="rds.highvaluedata.net")
   
   # Iterate through all catalogs
   for catalog_id, catalog in server.catalogs.items():
       print(f"\nCatalog: {catalog.name} ({catalog_id})")
       print(f"Description: {catalog.description}")
       print(f"Data Products: {len(catalog.data_products)}")
       
       # List first 5 data products
       for i, dp in enumerate(catalog.data_products[:5]):
           print(f"  {i+1}. {dp.name}")
       
       if len(catalog.data_products) > 5:
           print(f"  ... and {len(catalog.data_products) - 5} more")

Batch Processing Data Products
-------------------------------

Process all data products in a catalog:

.. code-block:: python

   from dartfx.mtnards import MtnaRdsServer
   import json
   
   server = MtnaRdsServer(host="rds.highvaluedata.net")
   catalog = server.catalogs['us_anes']
   
   metadata_collection = []
   
   for data_product in catalog.data_products:
       print(f"Processing: {data_product.name}")
       
       # Collect basic info
       metadata = {
           'id': data_product.id,
           'name': data_product.name,
           'description': data_product.description,
           'variable_count': len(data_product.variables),
           'uri': data_product.uri
       }
       
       metadata_collection.append(metadata)
   
   # Save to JSON
   with open('catalog_inventory.json', 'w') as f:
       json.dump(metadata_collection, f, indent=2)
   
   print(f"\nProcessed {len(metadata_collection)} data products")

Working with Variable Types
----------------------------

Analyze variables by their data types:

.. code-block:: python

   from dartfx.mtnards import MtnaRdsServer
   from collections import defaultdict
   
   server = MtnaRdsServer(host="rds.highvaluedata.net")
   catalog = server.catalogs['us_anes']
   data_product = catalog.data_products_by_id['anes_1948']
   
   # Group variables by type
   vars_by_type = defaultdict(list)
   
   for var_id, variable in data_product.variables.items():
       vars_by_type[variable.data_type].append(variable.name)
   
   # Display results
   for data_type, var_names in vars_by_type.items():
       print(f"\n{data_type} variables ({len(var_names)}):")
       for name in var_names[:5]:  # Show first 5
           print(f"  - {name}")
       if len(var_names) > 5:
           print(f"  ... and {len(var_names) - 5} more")

Exporting Variables to CSV
---------------------------

Export variable metadata to a CSV file:

.. code-block:: python

   from dartfx.mtnards import MtnaRdsServer
   import csv
   
   server = MtnaRdsServer(host="rds.highvaluedata.net")
   catalog = server.catalogs['us_anes']
   data_product = catalog.data_products_by_id['anes_1948']
   
   # Prepare data for CSV
   with open('variables.csv', 'w', newline='', encoding='utf-8') as f:
       writer = csv.writer(f)
       
       # Write header
       writer.writerow([
           'Variable ID', 'Name', 'Label', 'Type',
           'Has Classification', 'Description'
       ])
       
       # Write data
       for var_id, var in data_product.variables.items():
           writer.writerow([
               var_id,
               var.name,
               var.label or '',
               var.data_type,
               'Yes' if var.classification_stub else 'No',
               (var.description or '')[:100]  # Truncate long descriptions
           ])
   
   print(f"Exported {len(data_product.variables)} variables to variables.csv")

Working with Classifications
-----------------------------

Extract and analyze classification codes:

.. code-block:: python

   from dartfx.mtnards import MtnaRdsServer
   
   server = MtnaRdsServer(host="rds.highvaluedata.net")
   catalog = server.catalogs['us_anes']
   data_product = catalog.data_products_by_id['anes_1948']
   
   # Find variables with classifications
   classified_vars = [
       var for var in data_product.variables.values()
       if var.classification_stub
   ]
   
   print(f"Found {len(classified_vars)} classified variables\n")
   
   # Display classification details
   for var in classified_vars[:3]:  # First 3
       print(f"Variable: {var.label}")
       print(f"Classification: {var.classification.name}")
       print(f"Number of codes: {len(var.classification.codes)}")
       
       # Show first few codes
       for i, (code_id, code) in enumerate(list(var.classification.codes.items())[:5]):
           print(f"  {code.value}: {code.label}")
       
       if len(var.classification.codes) > 5:
           print(f"  ... and {len(var.classification.codes) - 5} more codes")
       print()

Generating Documentation for Multiple Datasets
-----------------------------------------------

Generate markdown documentation for multiple datasets:

.. code-block:: python

   from dartfx.mtnards import MtnaRdsServer
   from pathlib import Path
   
   server = MtnaRdsServer(host="rds.highvaluedata.net")
   catalog = server.catalogs['us_anes']
   
   # Create output directory
   output_dir = Path('docs_output')
   output_dir.mkdir(exist_ok=True)
   
   # Generate documentation for each data product
   for data_product in catalog.data_products[:5]:  # First 5
       print(f"Generating docs for: {data_product.name}")
       
       markdown = data_product.markdown()
       
       # Create filename from data product ID
       filename = f"{data_product.id}.md"
       filepath = output_dir / filename
       
       with open(filepath, 'w', encoding='utf-8') as f:
           f.write(markdown)
       
       print(f"  Saved to: {filepath}")
   
   print(f"\nGenerated documentation in {output_dir}/")

Creating a Dataset Catalog Index
---------------------------------

Build an HTML index of all datasets:

.. code-block:: python

   from dartfx.mtnards import MtnaRdsServer
   from pathlib import Path
   
   server = MtnaRdsServer(host="rds.highvaluedata.net")
   
   html_parts = [
       '<!DOCTYPE html>',
       '<html>',
       '<head>',
       '  <title>RDS Catalog Index</title>',
       '  <style>',
       '    body { font-family: sans-serif; margin: 40px; }',
       '    h1 { color: #333; }',
       '    h2 { color: #666; border-bottom: 2px solid #ddd; }',
       '    .dataset { margin: 10px 0; padding: 10px; background: #f5f5f5; }',
       '    .dataset-name { font-weight: bold; color: #0066cc; }',
       '  </style>',
       '</head>',
       '<body>',
       f'  <h1>{server.info.name}</h1>',
   ]
   
   for catalog_id, catalog in server.catalogs.items():
       html_parts.append(f'  <h2>{catalog.name}</h2>')
       html_parts.append(f'  <p>{catalog.description}</p>')
       
       for dp in catalog.data_products:
           html_parts.append('  <div class="dataset">')
           html_parts.append(f'    <div class="dataset-name">{dp.name}</div>')
           html_parts.append(f'    <div>{dp.description or "No description"}</div>')
           html_parts.append(f'    <div><small>ID: {dp.id} | Variables: {len(dp.variables)}</small></div>')
           html_parts.append('  </div>')
   
   html_parts.extend(['</body>', '</html>'])
   
   # Save to file
   with open('catalog_index.html', 'w', encoding='utf-8') as f:
       f.write('\n'.join(html_parts))
   
   print("Catalog index saved to catalog_index.html")

Working with RDF Graphs
-----------------------

Generate and query RDF graphs:

.. code-block:: python

   from dartfx.mtnards import MtnaRdsServer
   from dartfx.mtnards.dcat import MtnaRdsDcat
   from rdflib import Namespace
   
   server = MtnaRdsServer(host="rds.highvaluedata.net")
   catalog = server.catalogs['us_anes']
   data_product = catalog.data_products_by_id['anes_1948']
   
   # Create DCAT exporter
   dcat = MtnaRdsDcat(
       server=server,
       catalog=catalog,
       data_product=data_product,
       uri_style="uuid"
   )
   
   # Generate RDF graph
   graph = dcat.graph()
   
   # Query the graph
   DCAT = Namespace("http://www.w3.org/ns/dcat#")
   
   # Find all datasets
   for s, p, o in graph.triples((None, None, DCAT.Dataset)):
       print(f"Found dataset: {s}")
   
   # Export in different formats
   formats = ['turtle', 'xml', 'json-ld', 'n3']
   
   for fmt in formats:
       output = graph.serialize(format=fmt)
       filename = f'output.{fmt.replace("-", "_")}'
       with open(filename, 'w') as f:
           f.write(output)
       print(f"Saved: {filename}")

Caching and Performance
-----------------------

Work efficiently with caching:

.. code-block:: python

   from dartfx.mtnards import MtnaRdsServer
   import time
   
   server = MtnaRdsServer(host="rds.highvaluedata.net")
   
   # First access - fetches from server
   start = time.time()
   catalogs = server.catalogs
   first_time = time.time() - start
   print(f"First access: {first_time:.3f}s")
   
   # Second access - uses cache
   start = time.time()
   catalogs = server.catalogs
   cached_time = time.time() - start
   print(f"Cached access: {cached_time:.3f}s")
   print(f"Speed improvement: {first_time/cached_time:.1f}x faster")
   
   # Force refresh if needed
   catalogs = server.catalogs
   # Note: Currently refresh is automatic, caching happens at property level

Error Handling Best Practices
------------------------------

Robust error handling for production code:

.. code-block:: python

   from dartfx.mtnards import MtnaRdsServer
   import logging
   
   # Set up logging
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)
   
   def safe_connect(host, api_key=None):
       """Safely connect to an RDS server with error handling."""
       try:
           server = MtnaRdsServer(host=host, api_key=api_key)
           logger.info(f"Connected to {server.info.name}")
           return server
       except Exception as e:
           logger.error(f"Failed to connect to {host}: {e}")
           return None
   
   def safe_get_data_product(catalog, data_product_id):
       """Safely retrieve a data product with error handling."""
       try:
           if data_product_id in catalog.data_products_by_id:
               return catalog.data_products_by_id[data_product_id]
           else:
               logger.warning(f"Data product {data_product_id} not found")
               return None
       except Exception as e:
           logger.error(f"Error retrieving data product: {e}")
           return None
   
   # Usage
   server = safe_connect("rds.highvaluedata.net")
   if server and 'us_anes' in server.catalogs:
       catalog = server.catalogs['us_anes']
       dp = safe_get_data_product(catalog, 'anes_1948')
       if dp:
           print(f"Successfully loaded: {dp.name}")

Integration with Pandas
------------------------

Convert RDS data structures to Pandas DataFrames:

.. code-block:: python

   from dartfx.mtnards import MtnaRdsServer
   import pandas as pd
   
   server = MtnaRdsServer(host="rds.highvaluedata.net")
   catalog = server.catalogs['us_anes']
   data_product = catalog.data_products_by_id['anes_1948']
   
   # Create DataFrame of variables
   var_data = []
   for var_id, var in data_product.variables.items():
       var_data.append({
           'id': var_id,
           'name': var.name,
           'label': var.label,
           'type': var.data_type,
           'has_classification': bool(var.classification_stub)
       })
   
   df = pd.DataFrame(var_data)
   
   # Analyze
   print("Variable Type Distribution:")
   print(df['type'].value_counts())
   
   print("\nClassified Variables:")
   print(df['has_classification'].value_counts())
   
   # Export to Excel
   df.to_excel('variables_analysis.xlsx', index=False)
   print("\nExported to variables_analysis.xlsx")

More Examples
-------------

For more examples and use cases, check out:

* The `tests/ <https://github.com/DataArtifex/mtnards-toolkit/tree/main/tests>`_ directory in the repository
* `Example notebooks <https://github.com/DataArtifex/mtnards-toolkit/tree/main/examples>`_ (coming soon)
* The :doc:`api/core` for detailed API documentation
