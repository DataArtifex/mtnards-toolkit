Changelog
=========

All notable changes to the MTNA RDS Toolkit will be documented here.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[Unreleased]
------------

[0.2.1] - 2026-04-23
---------------------

Added
~~~~~

* Resource patching support for catalogs, data products, and variables via management PATCH endpoints
* New ``patching.py`` module with centralized patch contracts, field validation, alias normalization, and multilingual payload shaping
* New ``MtnaRdsPatchConflictError`` exception for HTTP ``409`` optimistic concurrency conflicts
* Resource-level ``patch()`` methods on ``MtnaRdsCatalog``, ``MtnaRdsDataProduct``, and ``MtnaRdsVariableStub``
* Focused test suite in ``tests/test_patch.py`` for normalization, routing, success sync, and conflict behavior

Changed
~~~~~~~

* Patch requests always include ``lastUpdate`` from the current resource state
* Successful patch operations synchronize in-memory resource objects from the full server response payload
* HTTP ``409`` conflict handling performs forced refresh and attaches latest state to the conflict exception
* ``MtnaRdsResource.last_update`` is typed as ``str | None`` to match server token semantics and subclass usage

Documentation
~~~~~~~~~~~~~

* Added patch usage examples and conflict handling guidance to README
* Added patch conflict exception to API reference
* Expanded technical implementation docs with patch architecture and endpoint contract

[0.2.0] - 2026-04-08
---------------------

Added
~~~~~

* Hierarchical CLI shell navigation with ``cd`` support for absolute (``/``) and relative paths
* Direct startup navigation via ``--path`` / ``-P`` options
* ``api`` telemetry command for real-time monitoring of backend request timing and status
* Enhanced ``variables`` view with statistical roles and code counts
* Command aliases for rapid navigation: ``vars`` and ``cls``
* Optimized metadata retrieval with lazy loading of classification codebooks

Changed
~~~~~~~

* Integrated premium terminal formatting via ``rich.table`` and ``rich.json``
* Improved hierarchical property resolution (e.g., ``show cat.prod@label``)
* Enhanced safety guards for interactive sessions (``Ctrl+C`` confirmation, deletion protection)

[0.1.0] - 2026-04-07
---------------------

[0.0.1] - 2024
--------------

Initial Release
~~~~~~~~~~~~~~~

Added
~~~~~

* Core RDS server connectivity
* Catalog and data product browsing
* Variable metadata access
* Croissant metadata generation
* DCAT/RDF export functionality
* Type-safe Pydantic models
* HTML to Markdown conversion
* Comprehensive test suite
* CI/CD with GitHub Actions

Core Features
~~~~~~~~~~~~~

* **MtnaRdsServer**: Client connection to MTNA RDS API endpoints
* **MtnaRdsCatalog**: Catalog browsing and management
* **MtnaRdsDataProduct**: Dataset metadata and variable access
* **MtnaRdsVariable**: Variable inspection with classification support
* **DCAT Export**: RDF graph generation for semantic web
* **Croissant Export**: ML-ready dataset documentation

Dependencies
~~~~~~~~~~~~

* Python 3.12+ support
* Pydantic 2.0+ for data modeling
* RDFLib 7.0+ for RDF graphs
* mlcroissant 1.0+ for Croissant metadata
* markdownify for HTML conversion

Development Tools
~~~~~~~~~~~~~~~~~

* Ruff for linting and formatting
* pytest for testing
* mypy for type checking
* pre-commit hooks
* Sphinx for documentation
* GitHub Actions CI/CD

Known Limitations
~~~~~~~~~~~~~~~~~

* Documentation is still being expanded
* Data querying and aggregation features are planned
* PyPI package not yet published

Migration Guide
---------------

This section will be populated when there are breaking changes between versions.

Future Plans
------------

Planned for 0.1.0
~~~~~~~~~~~~~~~~~

* Data querying and subsetting functionality
* Tabulation and aggregation tools
* Enhanced caching strategies
* Additional metadata format support
* First PyPI release

Planned for 0.2.0
~~~~~~~~~~~~~~~~~

* Performance optimizations
* Advanced query capabilities
* Additional export formats
* Plugin system for extensibility
* Enhanced error handling and recovery

Long-term Roadmap
~~~~~~~~~~~~~~~~~

* Data visualization integration
* Streaming data support
* Batch processing utilities
* Additional AI assistant integrations
* Web UI for dataset exploration

Deprecation Notices
-------------------

No deprecations in current version.

Security Updates
----------------

This project follows responsible security disclosure practices. Security vulnerabilities
will be documented here once fixed.

How to Upgrade
--------------

Since the package is not yet on PyPI, upgrade by pulling the latest changes:

.. code-block:: bash

   cd mtnards-toolkit
   git pull origin main
   uv sync  # or pip install -e .

For future PyPI releases:

.. code-block:: bash

   pip install --upgrade dartfx-mtnards

Version History
---------------

* **0.0.1** (2024) - Initial development release

Contributors
------------

* Pascal L.G.A. Heus - Initial work and maintainer

See the `GitHub contributors page <https://github.com/DataArtifex/mtnards-toolkit/graphs/contributors>`_
for a full list of contributors.

Links
-----

* `GitHub Repository <https://github.com/DataArtifex/mtnards-toolkit>`_
* `Issue Tracker <https://github.com/DataArtifex/mtnards-toolkit/issues>`_
* `Documentation <https://www.dataartifex.org/docs/dartfx-mtnards/>`_
* `DeepWiki AI Index <https://deepwiki.com/DataArtifex/mtnards-toolkit>`_
