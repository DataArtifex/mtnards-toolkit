# AI Agent Instructions

Welcome, fellow AI. This xfile provides context and instructions for working on this repository effectively.

The purpose of this package is to facilitate interaction with [Metadata Technology North America](https://www.mtna.us) a [Rich Data Services](https://www.richdataservices.com) server.

## Project Specifications

### Purpose & Scope

This package provides a Python toolkit for programmatic interaction with **MTNA Rich Data Services (RDS)** servers. It enables data scientists, developers, and AI systems to:

- **Discover & Access**: Query catalogs and retrieve datasets from MTNA RDS servers
- **Generate Metadata**: Produce Croissant ML-ready dataset documentation and DCAT/RDF semantic web representations
- **Analyze Variables**: Inspect data product variables, dimensions, measures, and classification codes
- **Aggregate Data**: Subset and tabulate data products using variables as dimensions and measures
- **Integrate with AI**: Expose RDS functionality via Model Context Protocol (MCP) for AI agent integration

### Core Data Model

The toolkit operates on these key entities:

- **MtnaRdsServer**: Client connection to an MTNA RDS API endpoint (host, authentication, base paths)
- **MtnaRdsCatalog**: A collection/library of data products within a server catalog
- **MtnaRdsDataProduct**: A dataset/data file with associated metadata and variables
- **MtnaRdsVariable**: A field/column within a data product (with type, classification codes, roles as dimension/measure)
- **MtnaRdsClassificationStub**: Classification/value set metadata for categorical variables

### Primary Use Cases for Agents

1. **Metadata Discovery**: List available catalogs, browse data products, search for datasets by name or description
2. **Documentation Generation**: Convert dataset metadata to standard formats (Croissant JSON-LD, DCAT/RDF Turtle)
3. **Data Profiling**: Retrieve variable information, data types, units, classification schemes
4. **Data Access**: Construct queries to subset and aggregate data products
5. **HVDN Integration**: Work with High-Value Data Network (HVDN) datasets, particularly for statistical and historical data
6. **MCP Tool Exposure**: Deploy the toolkit as an MCP server to enable Claude and other AI clients to query RDS servers directly

### Key Features & Capabilities

- **Server Connectivity**: Support for https-based RDS API endpoints with optional API key authentication
- **Metadata Formats**: Generate industry-standard metadata (Croissant for ML, DCAT for semantic web)
- **RDF Support**: Full RDF graph generation with customizable URI schemes (UUID, UUID URN, etc.)
- **Variable Classification**: Support for categorical variables with classification codes and statistical roles
- **HTML to Markdown**: Automatic conversion of HTML descriptions to Markdown for readability
- **Caching**: Intelligent caching of server info, catalogs, and catalog contents
- **Type Safety**: Pydantic-based models with full type hints for all public APIs

### Integration Points

- **DCAT (Data Catalog Vocabulary)**: Export datasets as DCAT RDF for semantic web compatibility
- **Croissant**: Support for ML-ready dataset documentation via mlcroissant library
- **RDFLib**: Semantic web integration with full RDF graph capabilities
- **Model Context Protocol**: MCP server integration for AI agent tools
- **HTTP Requests**: RESTful API interaction with MTNA RDS servers

### Development Constraints

- **No External Config**: Configuration via environment variables (.env) and constructors, no config files
- **Type Hints Required**: All public APIs must have complete type hints
- **Google/NumPy Docstrings**: Documentation must follow Sphinx-compatible style
- **Pathlib Preferred**: Use `pathlib.Path` over `os.path`
- **Pydantic Models**: Use Pydantic for all data structures
- **Test Coverage**: All features require accompanying pytest tests

## Project Stack

- **Language**: Python 3.12+ (Strictly required)
- **Dependency Management & Workflow**: [uv](https://github.com/astral-sh/uv) (Recommended) and [Hatch](https://hatch.pypa.io/).
- **Linting & Formatting**: [Ruff](https://beta.astral.sh/ruff/) (extremely fast linter/formatter).
- **Git Hooks**: [pre-commit](https://pre-commit.com/) (ensures code quality before commits).
- **Testing**: [pytest](https://docs.pytest.org/) with [coverage](https://coverage.readthedocs.io/).
- **Documentation**: [Sphinx](https://www.sphinx-doc.org/) with [MyST-Parser](https://myst-parser.readthedocs.io/) (Markdown support) and [Read the Docs theme](https://sphinx-rtd-theme.readthedocs.io/).
- **Version Control**: Git.

## Bootstrapping a New Project

To rename the project and package from the template defaults:
1. Run `./rename.sh "new-project-name" "new_package_name"`
2. Run `uv sync` to refresh the environment.
3. **DeepWiki**: Register the new project at [DeepWiki.com](https://deepwiki.com/) to enable AI-optimized documentation indexing.

## Environment Management

This project uses `hatch` for environment management, but `uv` is preferred for speed.

- To run tests: `uv run pytest` or `hatch run test`
- To check types: `hatch run types:check`
- To build docs: `hatch run docs:build`

## Coding Standards

- Follow PEP 8.
- Use type hints for all public APIs.
- Docstrings should be in Google style or NumPy style (Sphinx compatible).
- Prefer `pathlib` over `os.path`.
- Prefer Pydantic for modeling over Python data classs or other similar package
- Prefer Polars package for data management over Pandas or other similar package
- Strictly follow the project's Ruff configuration. Run `uv run ruff check .` and `uv run ruff format .` to ensure compliance before submitting changes.

## Testing Policy

- All new features must be accompanied by tests.
- Maintain or improve test coverage.
- Use `pytest` fixtures for setup/teardown.
- Tests are located in the `tests/` directory.

## Documentation Policy

- Documentation is located in the `docs/source` directory.
- Main documentation is in `.rst` or `.md` (via MyST).
- Keep `README.md` up to date with core installation and usage instructions.
- Keep a dedicated `IMPLEMENTATION.md` document up to date that describes the package/code technical implementation.
- Maintain `CHANGELOG.md` with every significant change, ensuring the latest version is always at the top using the version number as heading (e.g., `## [0.1.0]`). Use short concise bullet points.


## Version Management

- This project uses **dynamic versioning** via Hatch.
- The source of truth for the version is located in: `src/dartfx/hatch_foo/__about__.py`.
- To bump versions, modify that file manually or use `hatch version <segment>` (e.g., `hatch version minor`).
- Follow [Semantic Versioning (SemVer)](https://semver.org/).

## Secret Management

- **Local Development**: Use a `.env` file in the project root for local environment variables and secrets.
- **Loading**: Secrets are automatically loaded in tests via `tests/conftest.py` using `python-dotenv`.
- **Git Hygiene**: Never commit `.env` files. Ensure they are covered by `.gitignore`.
- **CI/CD**: Add secrets to GitHub Repository Secrets for use in GitHub Actions. Reference them in workflows as `${{ secrets.SECRET_NAME }}`.

## GitHub Actions CI/CD

- **CI**: Located in `.github/workflows/test.yml`. Runs tests and linting on push/PR to `main` across Ubuntu, macOS, and Windows.
- **Docs**: Located in `.github/workflows/sphinx.yaml`. Builds and deploys documentation to GitHub Pages on push to `main`.
- All workflows use `astral-sh/setup-uv` for fast execution and caching.

## Working with this Repo

1. **Analysis**: Always start by reviewing `pyproject.toml` and `src/` structure.
2. **Context**: Check `KIs` (Knowledge Items) if available for specific domain logic.
3. **Execution**: Use `uv` or `hatch` for running scripts and tests.
4. **Validation**: Always run `pytest` before finalizing changes.
