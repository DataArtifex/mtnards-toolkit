# Implementation Details

Technical implementation documentation for the `dartfx-mtnards` package.

## Package Structure

The package lives under `src/dartfx/mtnards/` as a namespace package (`dartfx.mtnards`). The source is organized into focused domain modules:

```
src/dartfx/mtnards/
├── __about__.py         # Package version (single source of truth)
├── __init__.py          # Public API exports
├── base.py              # Base classes: MtnaRdsError, MtnaRdsResource, MtnaRdsServerInfo
├── server.py            # MtnaRdsServer — API client and connection management
├── catalog.py           # MtnaRdsCatalog — catalog browsing and management
├── data_product.py      # MtnaRdsDataProduct — dataset metadata, variables, classifications
├── variable.py          # MtnaRdsVariableStub / MtnaRdsVariable — variable models
├── classification.py    # MtnaRdsClassificationStub / MtnaRdsClassification / MtnaRdsClassificationCode
├── process.py           # MtnaRdsProcess — server-side async process tracking
└── dcat.py              # DcatGenerator — DCAT/RDF metadata generation
```

## Module Responsibilities

### `base.py`

Defines the foundation types shared across all other modules:

- **`MtnaRdsError`** — Custom exception for API failures.
- **`MtnaRdsResource`** — Pydantic `BaseModel` with common fields (`uri`, `id`, `name`, `description`, `reference`, `revision_number`). Implements `__hash__` using `uri` so resources can be used in sets and as dict keys.
- **`MtnaRdsServerInfo`** — Lightweight model for server metadata (`name`, `released`, `version`).

### `server.py`

Entry point for all API interaction.

- **`MtnaRdsServer`** — Connects to an MTNA RDS host. Handles authentication (`api_key`), URL construction (`base_url`, `api_url`), and HTTP requests via `api_request()`.
- Catalogs are lazily loaded on first access via the `catalogs` property and can be refreshed with `refresh_catalogs()`.
- Provides methods for CRUD operations on catalogs and data products, file upload, DDI codebook retrieval, Postman collection export, and server-side process management.
- Uses `pathlib.Path` for file operations.

### `catalog.py`

- **`MtnaRdsCatalog`** — Represents a collection of data products. Attaches itself to child `MtnaRdsDataProduct` instances via a `model_validator`.
- Delegates most operations to its parent `MtnaRdsServer` instance (stored as `_server` private attribute).

### `data_product.py`

Largest module — models a dataset with its variables and classifications.

- **`MtnaRdsDataProduct`** — Lazy-loads `variables` and `classifications` as `dict[str, ...]` keyed by resource ID. Supports Croissant ML metadata generation, DDI Codebook export, Markdown documentation, and Postman collection generation.
- `load_metadata()` performs a bulk fetch of all variables and classifications in a single API call.
- `resolve_variables()` / `resolve_classifications()` upgrade stubs to full detail objects.

### `variable.py`

- **`MtnaRdsVariableStub`** — Lightweight variable summary with data type, classification reference, and dimensional roles.
- **`MtnaRdsVariable`** — Full variable detail (extends stub with `decimals`, `format`, `index`, positional fields).
- `resolve()` on stubs fetches full details and replaces the stub in the parent data product's dict.

### `classification.py`

- **`MtnaRdsClassificationStub`** — Lightweight classification with lazy-loaded codes.
- **`MtnaRdsClassification`** — Full classification detail (extends stub).
- **`MtnaRdsClassificationCode`** — Individual code value within a classification.
- Same stub-to-full resolution pattern as variables.

### `process.py`

- **`MtnaRdsProcess`** — Tracks server-side async operations (imports, deletions). Provides computed properties for status inspection (`completed_successfully`, `failed`, `inprogress`).

### `dcat.py`

- **`DcatGenerator`** — Builds DCAT (Data Catalog Vocabulary) RDF graphs from server catalogs and datasets. Uses `dartfx-rdf` and `dartfx-dcat` companion packages. Supports multiple URI generation strategies and Turtle serialization.

## Design Patterns

### Pydantic v2 Models

All domain models use Pydantic v2 `BaseModel` with:
- `Field(alias=...)` for camelCase JSON ↔ snake_case Python mapping.
- `PrivateAttr` for internal state not exposed in serialization.
- `computed_field` for derived properties that appear in serialization.
- `model_validator` for cross-field initialization logic (e.g., attaching parent references).
- `from __future__ import annotations` for deferred annotation evaluation.
- `model_config = ConfigDict(populate_by_name=True)` where needed for dual-name field access.

### Lazy Loading

Variables, classifications, classification codes, and catalogs are loaded on first access:
1. Private attribute starts as `None`.
2. Public `@computed_field` property checks for `None` and fetches from server.
3. Subsequent accesses return the cached value.

### Stub / Full Resolution

Variables and classifications follow a two-tier pattern:
1. **Stub** — Lightweight summary returned by list endpoints.
2. **Full** — Detailed object fetched by `resolve()` from the detail endpoint.
3. `resolve()` replaces the stub in the parent's dict with the full object.

### Circular Dependency Handling

Modules have mutual references (e.g., `MtnaRdsServer` ↔ `MtnaRdsCatalog`). This is resolved via:
- `from __future__ import annotations` (PEP 563) in every module.
- `TYPE_CHECKING` guards for imports only needed by type checkers.
- Deferred runtime imports inside methods where actual class references are needed.

## Public API

The `__init__.py` exports a curated set of classes:
- `MtnaRdsError`
- `MtnaRdsServer`
- `MtnaRdsCatalog`
- `MtnaRdsDataProduct`
- `MtnaRdsVariable`
- `MtnaRdsClassificationStub`

Internal classes (`MtnaRdsResource`, `MtnaRdsServerInfo`, `MtnaRdsVariableStub`, `MtnaRdsClassification`, `MtnaRdsClassificationCode`, `MtnaRdsProcess`) are accessible via their module paths but not promoted to package-level exports.

## Testing

Tests live in `tests/` and use `pytest`. The test suite requires a live MTNA RDS server (configured via `.env`). Fixtures in `conftest.py` set up server connections and load reference datasets. Test files cover:
- `test_model.py` — Model instantiation and server connectivity.
- `test_croissant.py` — Croissant ML metadata generation.
- `test_dcat.py` — DCAT/RDF graph generation.
- `test_markdown.py` — Markdown documentation output.

## Build & Tooling

- **Build backend**: Hatchling with dynamic versioning from `__about__.py`.
- **Namespace package**: `dartfx` namespace, `mtnards` sub-package.
- **Linting**: Ruff (line-length=120, target Python 3.12).
- **Type checking**: mypy.
- **Docs**: Sphinx with MyST-Parser and Read the Docs theme.
