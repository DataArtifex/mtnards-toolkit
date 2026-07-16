# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/) and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.2.2] - 2026-07-15

### Added
- Native RDS JSON (`rdsjson`) metadata import and export support.
- Interactive shell and top-level CLI commands: `import-rdsjson` and `export-rdsjson`.
- DDI-C XML metadata import workflow (`import_ddic_metadata`) and associated `import-ddic` CLI command.
- central utility helpers `import_metadata_rdsjson_workflow` and `import_ddic_metadata` in `utils.py`.

### Changed
- Migrated static type checker from mypy to pyrefly.
- Configured local pre-commit hooks running ruff and pyrefly via `scripts/precommit_uv_run.sh`.
- Updated GitHub Actions CI test workflow to run pyrefly type checking.
- Resolved all pyrefly static analysis errors and warnings across source code and test files.

## [0.2.1] - 2026-04-23

### Added
- Resource patching support for catalogs, data products, and variables via management PATCH endpoints
- New `patching.py` module with centralized patch contracts, field validation, alias normalization, and multilingual payload shaping
- New `MtnaRdsPatchConflictError` exception for HTTP `409` optimistic concurrency conflicts
- Resource-level `patch()` methods on `MtnaRdsCatalog`, `MtnaRdsDataProduct`, and `MtnaRdsVariableStub`
- Focused test suite in `tests/test_patch.py` for normalization, routing, success sync, and conflict behavior

### Changed
- Patch requests always include `lastUpdate` from the current resource state
- Successful patch operations now synchronize in-memory resource objects from the full server response payload
- HTTP `409` conflict handling now performs forced refresh and attaches latest state to conflict exception
- `MtnaRdsResource.last_update` is now typed as `str | None` to match server token semantics and subclass usage

### Documentation
- Updated README with patch examples and conflict-handling guidance
- Updated API docs to include patch conflict exception
- Expanded implementation documentation with patch architecture and endpoint contract

## [0.2.0] - 2026-04-08

### Added
- Hierarchical CLI shell navigation with `cd` support for absolute (`/`) and relative paths
- Direct startup navigation via `--path` / `-P` options
- `api` telemetry command displaying request history, status, and precise timing (ms)
- Multi-column `variables` view with statistical roles (Dim, Meas, Req, Wgt) and code counts
- Command aliases: `vars` (variables) and `cls` (classifications)
- Dedicated classification code table for `show <variable>` for better readability
- Standalone `--codes` / `-c` flag support (defaults to first 10 codes)
- Interactive shell exit confirmation on `Ctrl+C`

### Changed
- Refactored `resolve_path` to support standard filesystem semantics (`/` prefix)
- Optimized metadata display to lazy-load classification codes only when explicitly requested
- Integrated `rich.json` and `rich.table` for premium colorized terminal output
- Improved `show` command to handle hierarchical property resolution (e.g., `show cat.prod@label`)
- Enhanced `variables` and `classifications` shortcuts to respect global pagination flags

### Fixed
- Multiple `mypy` type annotation errors in command dispatch and resource resolution
- Safety guard preventing accidental deletion of the active product context

## [0.1.0]

### Added
- Core models: `MtnaRdsServer`, `MtnaRdsCatalog`, `MtnaRdsDataProduct`, `MtnaRdsVariable`, `MtnaRdsClassificationStub`
- `py.typed` PEP 561 marker for type checker support
- `types-requests` dev dependency for typed HTTP stubs
- `[tool.mypy]` configuration with `pydantic.mypy` plugin, namespace package support, and `prop-decorator` suppression
- Lazy-loaded variables and classifications with stub/full resolution pattern
- Croissant ML metadata generation (`get_croissant`)
- DCAT/RDF graph generation via `DcatGenerator`
- DDI Codebook export support
- Markdown documentation generation (`get_markdown`)
- Postman collection export
- Server-side process tracking (`MtnaRdsProcess`)
- File upload and data import workflows
- SQL-backed data product creation
- Complete type hints and docstrings on all public APIs
- `IMPLEMENTATION.md` with technical design documentation

### Changed
- Split monolithic `mtnards.py` into domain modules: `base`, `server`, `catalog`, `data_product`, `variable`, `classification`, `process`
- Variables and classifications stored as `dict[str, ...]` keyed by ID (was `list`)
- `catalogs` property on `MtnaRdsServer` split into read-only property and `refresh_catalogs()` method
- `changeLog` field renamed to `change_log` with `Field(alias="changeLog")`
- File operations use `pathlib.Path` instead of `os.path`
- Added `model_config = ConfigDict(populate_by_name=True)` to `MtnaRdsResource`, `MtnaRdsServer`, and `MtnaRdsProcess` so fields accept both alias and snake_case names
- `MtnaRdsResource.__eq__` now compares by URI to match `__hash__` contract
- `MtnaRdsClassificationCode.isPrivate` renamed to `is_private` with `Field(alias="isPrivate")`
- `MtnaRdsProcess.inprogress` renamed to `in_progress` for PEP 8 compliance
- `change_log` typed as `list[Any]` instead of bare `list`
- `get_classification_variables` return type corrected to `list[MtnaRdsVariableStub | MtnaRdsVariable]`
- `get_postman_collection` parameters now fully typed (`str | None`)
- `DcatGenerator.uri_generator` type annotation made optional and initialized to `None` in constructor
- `resolve_classifications` / `resolve_variables` isinstance checks now correctly skip already-resolved instances
- `_create_dcat_catalog` guards against `None` data_products before iterating
- `api_request` parameter types narrowed from bare `dict` to `dict[str, str]` / `dict[str, Any]`
- `get_ddi_codebook` uses `params` argument instead of manual query string concatenation
- `MtnaRdsCatalog.__str__` uses `model_dump()` instead of `vars()` for Pydantic v2 compatibility
- Sphinx docs now include `MtnaRdsProcess` and `MtnaRdsVariableStub` autoclass entries
- All `@computed_field` decorators now stack with `@property` for mypy compatibility
- `PrivateAttr(default=None)` lines annotated with `# type: ignore` for deferred initialization pattern
- `DcatGenerator.add_datasets` / `add_catalogs` accept `Iterable` instead of `list`
- `MtnaRdsProcess.__str__` uses `model_dump()` instead of `vars()` for Pydantic v2 compatibility
- `resolve()` methods set `_data_product` after construction instead of as constructor kwarg
- `MtnaRdsClassificationCode.id` override annotated with `# type: ignore[assignment]`
- `api_endpoint` return type guaranteed as `str` (handles `None` base_path/api_path)
- `catalogs` property asserts non-None after `_load_catalogs()` for type narrowing
- `code_count` comparison guarded against `None` in `get_croissant`
- `classification` access guarded against `None` in `get_markdown` and `load_metadata`

### Fixed
- `get_variable_by_uri` / `get_classification_by_uri` now iterate `.values()` instead of dict keys
- `resolve_variables` / `resolve_classifications` now iterate `.values()` instead of dict keys
- `resolve_variables` / `resolve_classifications` iterate `list(...)` snapshot to avoid dict mutation during iteration
- Lookup methods (`get_*_by_uri`, `get_*_by_id`) return explicit `None` when not found
- Fixed typo `import_confifguration` → `import_configuration` in `MtnaRdsServer.import_file`
- Wrong `isinstance` check in `load_metadata`: `MtnaRdsClassificationStub` → `MtnaRdsClassification`
- `get_data_product_by_uri` / `get_data_product_by_id` now guard against `None` data_products
- `wait_for_process` raises `MtnaRdsError` on timeout instead of returning `None`
- `ensure_https_host` validator guards against `None` host value

### Removed
- Unused `MtnaRdsProcessManager` and `MtnaRdsManagedProcess` classes
- MCP server prototype (moved to separate project)
