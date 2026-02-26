DCAT/RDF API Reference
======================

This page documents the DCAT and RDF export functionality.

Overview
--------

The DCAT module provides functionality to export MTNA RDS metadata as RDF graphs following 
the `Data Catalog Vocabulary (DCAT) <https://www.w3.org/TR/vocab-dcat/>`_ standard.

Main Class
----------

.. autoclass:: dartfx.mtnards.dcat.MtnaRdsDcat
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

URI Styles
----------

The DCAT exporter supports different URI generation styles:

* ``"uuid"`` - UUID without namespace (e.g., ``123e4567-e89b-12d3-a456-426614174000``)
* ``"uuid_urn"`` - UUID as URN (e.g., ``urn:uuid:123e4567-e89b-12d3-a456-426614174000``)
* ``"hostname"`` - Based on server hostname (e.g., ``https://rds.example.com/resource/123``)

Example Usage
-------------

Basic RDF Generation
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from dartfx.mtnards import MtnaRdsServer
   from dartfx.mtnards.dcat import MtnaRdsDcat
   
   server = MtnaRdsServer(host="rds.highvaluedata.net")
   catalog = server.catalogs['us-anes']
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
   
   # Serialize to Turtle format
   turtle = graph.serialize(format='turtle')
   print(turtle)

Different Output Formats
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Turtle (readable text format)
   turtle = graph.serialize(format='turtle')
   
   # XML/RDF
   xml = graph.serialize(format='xml')
   
   # JSON-LD
   jsonld = graph.serialize(format='json-ld')
   
   # N-Triples
   nt = graph.serialize(format='nt')
   
   # N3
   n3 = graph.serialize(format='n3')

Querying RDF Graphs
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from rdflib import Namespace, RDF
   
   DCAT = Namespace("http://www.w3.org/ns/dcat#")
   DCT = Namespace("http://purl.org/dc/terms/")
   
   # Query for all datasets
   for subj in graph.subjects(RDF.type, DCAT.Dataset):
       title = graph.value(subj, DCT.title)
       description = graph.value(subj, DCT.description)
       print(f"Dataset: {title}")
       print(f"Description: {description}")
       print()

RDF Namespaces
--------------

The DCAT exporter uses the following standard namespaces:

* **DCAT**: http://www.w3.org/ns/dcat# - Data Catalog Vocabulary
* **DCT**: http://purl.org/dc/terms/ - Dublin Core Terms
* **FOAF**: http://xmlns.com/foaf/0.1/ - Friend of a Friend
* **RDF**: http://www.w3.org/1999/02/22-rdf-syntax-ns# - RDF Syntax
* **RDFS**: http://www.w3.org/2000/01/rdf-schema# - RDF Schema
* **XSD**: http://www.w3.org/2001/XMLSchema# - XML Schema

DCAT Classes Used
-----------------

The exporter generates instances of these DCAT classes:

* ``dcat:Catalog`` - Represents the RDS catalog
* ``dcat:Dataset`` - Represents individual data products
* ``dcat:Distribution`` - Data access information
* ``dcat:DataService`` - RDS server information
* ``foaf:Agent`` - Publishers and creators

Properties
----------

Common properties included in the RDF output:

* ``dct:title`` - Dataset title
* ``dct:description`` - Dataset description
* ``dct:identifier`` - Dataset identifier
* ``dct:issued`` - Release date
* ``dct:modified`` - Last modification date
* ``dct:publisher`` - Publishing organization
* ``dcat:keyword`` - Keywords/tags
* ``dcat:theme`` - Subject categories
* ``dcat:contactPoint`` - Contact information
* ``dcat:distribution`` - Access URLs

Integration with RDFLib
------------------------

The module uses `RDFLib <https://rdflib.readthedocs.io/>`_ for RDF graph manipulation:

.. code-block:: python

   from rdflib import Graph, URIRef, Literal, Namespace
   
   # Create custom graph
   g = Graph()
   
   # Add custom triples
   CUSTOM = Namespace("http://example.org/ns#")
   subject = URIRef("http://example.org/dataset/123")
   g.add((subject, CUSTOM.customProperty, Literal("value")))
   
   # Merge with DCAT graph
   dcat_graph = dcat.graph()
   dcat_graph += g
   
   # Serialize merged graph
   print(dcat_graph.serialize(format='turtle'))

Best Practices
--------------

Choosing URI Styles
~~~~~~~~~~~~~~~~~~~~

* Use ``"uuid_urn"`` for maximum interoperability
* Use ``"hostname"`` for human-readable URIs
* Use ``"uuid"`` for compact identifiers

Performance Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~

* RDF graph generation involves API calls to the RDS server
* Results are cached where possible
* For large catalogs, consider generating RDF incrementally

Validation
~~~~~~~~~~

Validate generated RDF:

.. code-block:: python

   # Check graph size
   print(f"Triples: {len(graph)}")
   
   # Verify key properties exist
   from rdflib import RDF
   DCAT = Namespace("http://www.w3.org/ns/dcat#")
   
   datasets = list(graph.subjects(RDF.type, DCAT.Dataset))
   print(f"Datasets found: {len(datasets)}")

Related Standards
-----------------

* `DCAT Version 2 <https://www.w3.org/TR/vocab-dcat-2/>`_
* `DCAT Version 3 <https://www.w3.org/TR/vocab-dcat-3/>`_
* `Dublin Core Metadata Initiative <https://www.dublincore.org/>`_
* `schema.org <https://schema.org/>`_
