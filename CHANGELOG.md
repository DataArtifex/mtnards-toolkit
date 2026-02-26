# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/) and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.0.1]

### Added
- Core models: `MtnaRdsServer`, `MtnaRdsCatalog`, `MtnaRdsDataProduct`, `MtnaRdsVariable`, `MtnaRdsClassificationStub`
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
