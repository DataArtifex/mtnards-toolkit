# MTNA Rich Data Services Toolkit

[![Development Status](https://img.shields.io/badge/status-early%20release-orange.svg)](https://github.com/DataArtifex/mtnards-toolkit)
[![Documentation](https://img.shields.io/badge/docs-blue)](https://www.dataartifex.org/docs/dartfx-mtnards/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/DataArtifex/mtnards-toolkit)
[![Package Status](https://img.shields.io/badge/PyPI-not%20published-lightgrey)](https://github.com/DataArtifex/mtnards-toolkit)
[![CI](https://github.com/DataArtifex/mtnards-toolkit/actions/workflows/test.yml/badge.svg)](https://github.com/DataArtifex/mtnards-toolkit/actions/workflows/test.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](code_of_conduct.md)
[![License](https://img.shields.io/github/license/DataArtifex/mtnards-toolkit.svg)](https://github.com/DataArtifex/mtnards-toolkit/blob/main/LICENSE.txt)

**This project is in its early development stages, so stability is not guaranteed, and documentation is limited. We welcome your feedback and contributions as we refine and expand this project together!**

## Overview

A Python toolkit for programmatic interaction with **[Metadata Technology North America (MTNA)](https://www.mtna.us)** [Rich Data Services (RDS)](https://www.richdataservices.com) servers. This package enables data scientists, developers, and AI systems to discover, access, and analyze datasets from MTNA RDS servers with full support for metadata standards like Croissant and DCAT.

### Key Features

- **Server Connectivity**: Connect to MTNA RDS API endpoints with optional API key authentication
- **Metadata Discovery**: Browse catalogs, search data products, and explore variables
- **Standard Metadata Formats**: Generate Croissant JSON-LD for ML pipelines and DCAT/RDF for semantic web integration
- **Data Access**: Query variables, inspect classification codes, and subset data products
- **AI Integration**: Model Context Protocol (MCP) server for Claude and other AI assistants
- **Type Safety**: Full type hints and Pydantic-based models for all APIs
- **HTML to Markdown**: Automatic conversion of dataset descriptions for improved readability

### Core Components

- **MtnaRdsServer**: Client connection to an MTNA RDS API endpoint
- **MtnaRdsCatalog**: Collection of data products within a server catalog
- **MtnaRdsDataProduct**: Individual dataset with associated metadata and variables
- **MtnaRdsVariable**: Data field/column with type information and classification codes
- **DCAT Export**: Generate RDF graphs for semantic web interoperability
- **Croissant Export**: Create ML-ready dataset documentation


## Installation

### Requirements

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### PyPI Release

Once stable, this package will be officially released and distributed through [PyPI](https://pypi.org/). Stay tuned for updates!

### Local Development Installation

For now, you can install the package locally for development:

#### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/DataArtifex/mtnards-toolkit.git
cd mtnards-toolkit

# Sync dependencies and install package in editable mode
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

#### Using pip

```bash
# Clone the repository
git clone https://github.com/DataArtifex/mtnards-toolkit.git
cd mtnards-toolkit

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux

# Install in editable mode
pip install -e .
```

### MCP Server Installation

To use the Model Context Protocol (MCP) server features:

```bash
# Install with MCP dependencies
pip install -e ".[mcp]"
```

## Usage

### Basic Example: Connecting to an RDS Server

```python
from dartfx.mtnards import MtnaRdsServer

# Connect to a public RDS server
server = MtnaRdsServer(host="rds.highvaluedata.net")

# Get server information
print(server.info)

# List available catalogs
for catalog_id, catalog in server.catalogs.items():
    print(f"{catalog_id}: {catalog.name}")
```

### Working with Catalogs and Data Products

```python
# Get a specific catalog
catalog = server.catalogs['us_anes']
print(f"Catalog: {catalog.name}")
print(f"Description: {catalog.description}")

# Browse data products in the catalog
for data_product in catalog.data_products:
    print(f"- {data_product.id}: {data_product.name}")
```

### Exploring Data Product Variables

```python
# Get a specific data product
data_product = catalog.data_products_by_id['anes_1948']

# Access variables
for variable in data_product.variables.values():
    print(f"Variable: {variable.name}")
    print(f"  Type: {variable.data_type}")
    print(f"  Label: {variable.label}")
```

### Generating Croissant Metadata

```python
# Generate Croissant JSON-LD for ML workflows
croissant_metadata = data_product.croissant()

# Save to file
with open('dataset.croissant.jsonld', 'w') as f:
    f.write(croissant_metadata.to_json())
```

### Exporting DCAT RDF

```python
from dartfx.mtnards.dcat import MtnaRdsDcat

# Create DCAT exporter
dcat = MtnaRdsDcat(
    server=server,
    catalog=catalog,
    data_product=data_product,
    uri_style="uuid"  # or "uuid_urn", "hostname", etc.
)

# Generate RDF graph
graph = dcat.graph()

# Export as Turtle
turtle = graph.serialize(format='turtle')
print(turtle)
```

### Using API Keys

```python
# Connect with API key authentication
server = MtnaRdsServer(
    host="rds.example.com",
    api_key="your-api-key-here"
)
```

### Environment Variables

For production use, set credentials via environment variables:

```bash
export MTNA_RDS_HOST="rds.highvaluedata.net"
export MTNA_RDS_API_KEY="your-api-key"
```

Then load them in your code:

```python
import os
from dartfx.mtnards import MtnaRdsServer

server = MtnaRdsServer(
    host=os.getenv("MTNA_RDS_HOST"),
    api_key=os.getenv("MTNA_RDS_API_KEY")
)
```

### MCP Server Usage

The toolkit includes a Model Context Protocol (MCP) server for integration with Claude and other AI assistants:

```bash
# Start the MCP server
python -m dartfx.mtnards.mcp.server
```

Configure your Claude Desktop to use the MCP server by adding to `claude_desktop_config.json`:

```json
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
```

Once configured, Claude can:
- Browse available catalogs and data products
- Retrieve dataset metadata and documentation
- Explore variables and their properties
- Help construct data queries

## Features & Capabilities

### Metadata Standards Support

- **Croissant**: Generate ML-ready dataset documentation compatible with the [Croissant specification](https://github.com/mlcommons/croissant)
- **DCAT (Data Catalog Vocabulary)**: Export datasets as RDF graphs for semantic web interoperability
- **RDF/Turtle**: Full RDF graph generation with customizable URI schemes

### Data Discovery

- List all catalogs on an RDS server
- Browse data products within catalogs
- Search datasets by name or description
- Retrieve comprehensive metadata for datasets

### Variable Exploration

- Inspect variable types, labels, and descriptions
- Access classification codes for categorical variables
- Identify dimension and measure roles for data aggregation
- Convert HTML descriptions to Markdown automatically

### Integration Points

- **Model Context Protocol (MCP)**: AI assistant integration
- **HTTP/REST API**: Full RESTful API support for MTNA RDS servers
- **Type Safety**: Pydantic models with complete type hints
- **Caching**: Intelligent caching of server info and catalog contents

## Roadmap

- [x] Core RDS API connectivity
- [x] Catalog and data product browsing
- [x] Variable metadata access
- [x] Croissant metadata generation
- [x] DCAT/RDF export
- [x] MCP server implementation
- [ ] Data querying and subsetting
- [ ] Tabulation and aggregation tools
- [ ] PyPI package release
- [ ] Comprehensive documentation
- [ ] Additional metadata format support
- [ ] Performance optimizations and caching strategies

## Contributing

We welcome contributions! Here's how to get started:

### Development Setup

```bash
# Clone the repository
git clone https://github.com/DataArtifex/mtnards-toolkit.git
cd mtnards-toolkit

# Install development dependencies with uv (recommended)
uv sync

# Or with pip
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=dartfx.mtnards

# Or using hatch
hatch run test
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type checking
hatch run types:check
```

### Contribution Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes following the coding standards in [AGENTS.md](AGENTS.md)
4. Add tests for new functionality
5. Ensure all tests pass and code is properly formatted
6. Commit your changes: `git commit -am 'Add some feature'`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Submit a pull request

### Coding Standards

- Follow PEP 8 style guidelines
- Use type hints for all public APIs
- Write docstrings in Google or NumPy style
- Prefer `pathlib` over `os.path`
- Use Pydantic for data modeling
- Maintain or improve test coverage

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

## Documentation

- **Project Documentation**: https://www.dataartifex.org/docs/dartfx-mtnards/
- **API Reference**: Coming soon
- **DeepWiki AI Index**: https://deepwiki.com/DataArtifex/mtnards-toolkit
- **MTNA RDS**: https://www.richdataservices.com
- **High-Value Data Network**: https://highvaluedata.net/

## Support & Community

- **Issues**: [GitHub Issues](https://github.com/DataArtifex/mtnards-toolkit/issues)
- **Discussions**: [GitHub Discussions](https://github.com/DataArtifex/mtnards-toolkit/discussions)
- **Code of Conduct**: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## License

MIT License - Copyright (c) 2024 Pascal L.G.A. Heus

See [LICENSE.txt](LICENSE.txt) for full details.

---

**Note**: This is an early-stage project under active development. APIs may change, and documentation is still being expanded. Contributions and feedback are highly appreciated!
