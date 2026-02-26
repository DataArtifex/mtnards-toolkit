Changelog
=========

All notable changes to the MTNA RDS Toolkit will be documented here.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[Unreleased]
------------

Added
~~~~~

* Comprehensive Sphinx documentation
* Installation guide with uv and pip instructions
* Quick start guide with examples
* Detailed API reference
* MCP server user guide
* Contributing guidelines

Changed
~~~~~~~

* Improved README with comprehensive project information
* Enhanced documentation structure

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
* Model Context Protocol (MCP) server implementation
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
* **MCP Server**: AI assistant integration via Model Context Protocol

Dependencies
~~~~~~~~~~~~

* Python 3.12+ support
* Pydantic 2.0+ for data modeling
* RDFLib 7.0+ for RDF graphs
* mlcroissant 1.0+ for Croissant metadata
* FastMCP 1.6+ for MCP server
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
* Some MCP tools are not yet implemented (commented out)
* Data querying and aggregation features are planned
* PyPI package not yet published

Migration Guide
---------------

This section will be populated when there are breaking changes between versions.

Future Plans
------------

Planned for 0.1.0
~~~~~~~~~~~~~~~~~

* Complete MCP server tool implementation
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
