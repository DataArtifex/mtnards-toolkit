MTNA Rich Data Services Toolkit
================================

.. image:: https://img.shields.io/badge/status-early%20release-orange.svg
   :target: https://github.com/DataArtifex/mtnards-toolkit
   :alt: Development Status

.. image:: https://github.com/DataArtifex/mtnards-toolkit/actions/workflows/test.yml/badge.svg
   :target: https://github.com/DataArtifex/mtnards-toolkit/actions/workflows/test.yml
   :alt: CI Status

.. image:: https://img.shields.io/github/license/DataArtifex/mtnards-toolkit.svg
   :target: https://github.com/DataArtifex/mtnards-toolkit/blob/main/LICENSE.txt
   :alt: License

**A Python toolkit for programmatic interaction with MTNA Rich Data Services (RDS) servers.**

This package enables data scientists, developers, and AI systems to discover, access, and analyze 
datasets from `Metadata Technology North America (MTNA) <https://www.mtna.us>`_ 
`Rich Data Services (RDS) <https://www.richdataservices.com>`_ servers with full support for 
metadata standards like Croissant and DCAT.

.. warning::
   This project is in its early development stages. Stability is not guaranteed, and documentation 
   is still being expanded. We welcome your feedback and contributions!

Key Features
------------

* **Server Connectivity**: Connect to MTNA RDS API endpoints with optional API key authentication
* **Metadata Discovery**: Browse catalogs, search data products, and explore variables
* **Standard Metadata Formats**: Generate Croissant JSON-LD for ML pipelines and DCAT/RDF for semantic web integration
* **Data Access**: Query variables, inspect classification codes, and subset data products
* **AI Integration**: Model Context Protocol (MCP) server for Claude and other AI assistants
* **Type Safety**: Full type hints and Pydantic-based models for all APIs
* **HTML to Markdown**: Automatic conversion of dataset descriptions for improved readability

Quick Example
-------------

.. code-block:: python

   from dartfx.mtnards import MtnaRdsServer

   # Connect to a public RDS server
   server = MtnaRdsServer(host="rds.highvaluedata.net")

   # List available catalogs
   for catalog_id, catalog in server.catalogs.items():
       print(f"{catalog_id}: {catalog.name}")

   # Access a data product
   catalog = server.catalogs['us_anes']
   data_product = catalog.data_products_by_id['anes_1948']

   # Generate Croissant metadata
   croissant = data_product.croissant()

Documentation Contents
----------------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   examples
   mcp_server

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/core
   api/dcat
   api/mcp

.. toctree::
   :maxdepth: 1
   :caption: Development

   contributing
   changelog

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Resources
=========

* **GitHub Repository**: https://github.com/DataArtifex/mtnards-toolkit
* **Issue Tracker**: https://github.com/DataArtifex/mtnards-toolkit/issues
* **DeepWiki AI Index**: https://deepwiki.com/DataArtifex/mtnards-toolkit
* **MTNA RDS**: https://www.richdataservices.com
* **High-Value Data Network**: https://highvaluedata.net/
