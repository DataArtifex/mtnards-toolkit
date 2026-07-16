"""Patching helpers for MTNA RDS resources."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from .base import MtnaRdsError

ResourceKind = Literal["catalog", "data_product", "variable"]


class PatchRequest(BaseModel):
    """Normalized patch request payload and destination."""

    model_config = ConfigDict(frozen=True)

    resource_kind: ResourceKind
    resource_uri: str
    path: str
    payload: dict[str, Any]


class PatchSpec(BaseModel):
    """Patch constraints for a resource kind."""

    model_config = ConfigDict(frozen=True)

    non_patchable_fields: set[str]
    multilingual_fields: set[str]


PATCH_SPECS: dict[ResourceKind, PatchSpec] = {
    "catalog": PatchSpec(
        non_patchable_fields={"uri", "last_update", "id"},
        multilingual_fields={"name", "description", "abbreviation", "keywords"},
    ),
    "data_product": PatchSpec(
        non_patchable_fields={"uri", "last_update", "id"},
        multilingual_fields={"name", "description", "abbreviation"},
    ),
    "variable": PatchSpec(
        non_patchable_fields={"uri", "last_update", "id"},
        multilingual_fields={"name", "description", "label"},
    ),
}


def build_patch_request(resource: Any, updates: dict[str, Any], lang: str = "en") -> PatchRequest:
    """Builds a normalized patch request for a resource."""
    resource_kind = _get_resource_kind(resource)
    spec = PATCH_SPECS[resource_kind]
    alias_map, reverse_alias_map = _get_alias_maps(resource.__class__)

    payload: dict[str, Any] = {}
    for input_key, value in updates.items():
        python_key = reverse_alias_map.get(input_key)
        if python_key is None:
            raise MtnaRdsError(f"Unsupported patch field: {input_key}")

        if python_key in spec.non_patchable_fields:
            raise MtnaRdsError(f"Field is not patchable: {input_key}")

        if python_key not in resource.__class__.model_fields:
            raise MtnaRdsError(f"Unknown patch field: {input_key}")

        api_key = alias_map.get(python_key, python_key)
        if python_key in spec.multilingual_fields:
            payload[api_key] = _normalize_multilingual_value(api_key, value, lang)
        else:
            payload[api_key] = value

    payload["lastUpdate"] = _normalize_last_update_token(getattr(resource, "last_update", None))
    payload["uri"] = str(resource.uri)

    resource_uri = str(resource.uri)
    return PatchRequest(
        resource_kind=resource_kind,
        resource_uri=resource_uri,
        path=_build_management_path(resource, resource_kind),
        payload=payload,
    )


def refresh_resource_from_server(resource: Any) -> Any | None:
    """Fetches the latest state for a resource from the server."""
    resource_kind = _get_resource_kind(resource)

    if resource_kind == "catalog":
        return _refresh_catalog_resource(resource)

    if resource_kind == "data_product":
        return _refresh_data_product_resource(resource)

    return _refresh_variable_resource(resource)


def _refresh_catalog_resource(resource: Any) -> Any | None:
    """Refreshes and returns the latest catalog resource."""
    server = getattr(resource, "_server", None)
    if server is None:
        return None
    return _refresh_catalog(server, catalog_uri=str(resource.uri), catalog_id=getattr(resource, "id", None))


def _refresh_data_product_resource(resource: Any) -> Any | None:
    """Refreshes and returns the latest data product resource."""
    catalog = getattr(resource, "_catalog", None)
    refreshed_catalog = _refresh_parent_catalog(catalog)
    if refreshed_catalog is None:
        return None

    refreshed_data_product = refreshed_catalog.get_data_product_by_uri(str(resource.uri))
    if refreshed_data_product is not None:
        return refreshed_data_product
    return refreshed_catalog.get_data_product_by_id(resource.id)


def _refresh_variable_resource(resource: Any) -> Any | None:
    """Refreshes and returns the latest variable resource."""
    data_product = getattr(resource, "_data_product", None)
    if data_product is None:
        return None

    refreshed_catalog = _refresh_parent_catalog(getattr(data_product, "_catalog", None))
    if refreshed_catalog is None:
        return None

    refreshed_product = refreshed_catalog.get_data_product_by_uri(str(data_product.uri))
    if refreshed_product is None:
        refreshed_product = refreshed_catalog.get_data_product_by_id(data_product.id)
    if refreshed_product is None:
        return None

    refreshed_variable = refreshed_product.get_variable_by_uri(str(resource.uri))
    if refreshed_variable is None:
        refreshed_variable = refreshed_product.get_variable_by_id(resource.id)
    return refreshed_variable


def _refresh_parent_catalog(catalog: Any) -> Any | None:
    """Refreshes the parent catalog for a nested resource."""
    if catalog is None:
        return None

    server = getattr(catalog, "_server", None)
    if server is None:
        return None

    return _refresh_catalog(
        server,
        catalog_uri=str(catalog.uri),
        catalog_id=getattr(catalog, "id", None),
    )


def _refresh_catalog(server: Any, catalog_uri: str, catalog_id: Any) -> Any | None:
    """Refreshes catalog list and returns a fully refreshed catalog object.

    URI is treated as canonical; ID is only used as a fallback for refetch.
    """
    server.refresh_catalogs()

    catalog = server.get_catalog_by_uri(catalog_uri)
    resolved_id = getattr(catalog, "id", None)
    if isinstance(resolved_id, str) and resolved_id:
        return server.get_catalog_by_id(resolved_id, fetch=True)

    if isinstance(catalog_id, str) and catalog_id:
        return server.get_catalog_by_id(catalog_id, fetch=True)

    return None


def sync_resource_from_payload(resource: Any, payload: dict[str, Any]) -> Any:
    """Updates a resource instance in-place from a full server payload."""
    normalized_payload = _normalize_response_payload(resource, payload)

    # PATCH responses may be partial; merge onto current state to avoid
    # dropping fields that are omitted by the server (e.g. classificationId).
    baseline_payload = resource.model_dump(by_alias=True, exclude_computed_fields=True)
    merged_payload = {**baseline_payload, **normalized_payload}
    updated = resource.__class__(**merged_payload)

    for field_name in resource.__class__.model_fields:
        setattr(resource, field_name, getattr(updated, field_name))

    if hasattr(resource, "_server") and getattr(resource, "_server", None) is not None:
        if getattr(resource, "data_products", None):
            for product in resource.data_products:
                product._catalog = resource

    if hasattr(resource, "_data_product") and getattr(resource, "_data_product", None) is not None:
        updated_data_product = resource._data_product
        resource._data_product = updated_data_product

    if hasattr(resource, "_catalog") and getattr(resource, "_catalog", None) is not None:
        updated_catalog = resource._catalog
        resource._catalog = updated_catalog

    return resource


def sync_resource_from_resource(resource: Any, source_resource: Any) -> Any:
    """Updates a resource in-place from another resource instance."""
    if not hasattr(source_resource, "model_dump"):
        raise MtnaRdsError("Cannot sync from source resource without model_dump")
    payload = source_resource.model_dump(by_alias=True, exclude_computed_fields=True)
    return sync_resource_from_payload(resource, payload)


def _normalize_response_payload(resource: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """Normalizes PATCH response payload for model validation.

    Management endpoints may return multilingual properties as facet lists, while
    model fields are plain strings. Convert those facet lists to plain values.
    """
    normalized = dict(payload)

    resource_kind = _get_resource_kind(resource)
    alias_map, _ = _get_alias_maps(resource.__class__)

    _normalize_payload_for_kind(normalized, resource_kind, alias_map=alias_map)

    return normalized


def _normalize_payload_for_kind(
    payload: dict[str, Any],
    resource_kind: ResourceKind,
    *,
    alias_map: dict[str, str] | None = None,
) -> None:
    """Normalizes a payload in-place according to the patch spec for a resource kind."""
    spec = PATCH_SPECS[resource_kind]

    for field_name in spec.multilingual_fields:
        for key in _field_keys(field_name, alias_map):
            value = payload.get(key)
            if isinstance(value, list) and _is_valid_facet_list(value):
                payload[key] = _facet_list_to_string(value, preferred_facet_id="en")


def _field_keys(field_name: str, alias_map: dict[str, str] | None = None) -> set[str]:
    """Returns likely payload keys for a field name."""
    keys = {field_name, _snake_to_camel(field_name)}
    if alias_map:
        keys.add(alias_map.get(field_name, field_name))
    return keys


def _snake_to_camel(value: str) -> str:
    """Converts snake_case field names to lowerCamelCase API keys."""
    if "_" not in value:
        return value
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


def _facet_list_to_string(facets: list[dict[str, Any]], preferred_facet_id: str = "en") -> str:
    """Converts a valid facet list to a plain string value."""
    for facet in facets:
        if facet.get("facetId") == preferred_facet_id and isinstance(facet.get("value"), str):
            return facet["value"]
    first_value = facets[0].get("value")
    return first_value if isinstance(first_value, str) else ""


def _build_management_path(resource: Any, resource_kind: ResourceKind) -> str:
    if resource_kind == "catalog":
        return f"management/catalog/{resource.uri}"

    if resource_kind == "data_product":
        catalog = getattr(resource, "_catalog", None)
        if catalog is None:
            raise MtnaRdsError("Data product is not attached to a catalog")
        return f"management/catalog/{catalog.uri}/product/{resource.uri}"

    return f"management/variable/{resource.uri}"


def _get_alias_maps(resource_class: type[Any]) -> tuple[dict[str, str], dict[str, str]]:
    alias_map: dict[str, str] = {}
    reverse_alias_map: dict[str, str] = {}

    for field_name, model_field in resource_class.model_fields.items():
        alias = model_field.alias or field_name
        alias_map[field_name] = alias
        reverse_alias_map[field_name] = field_name
        reverse_alias_map[alias] = field_name

    return alias_map, reverse_alias_map


def _get_resource_kind(resource: Any) -> ResourceKind:
    from .catalog import MtnaRdsCatalog
    from .data_product import MtnaRdsDataProduct
    from .variable import MtnaRdsVariableStub

    if isinstance(resource, MtnaRdsCatalog):
        return "catalog"
    if isinstance(resource, MtnaRdsDataProduct):
        return "data_product"
    if isinstance(resource, MtnaRdsVariableStub):
        return "variable"
    raise MtnaRdsError(f"Unsupported resource type for patching: {type(resource).__name__}")


def _normalize_last_update_token(last_update: Any) -> str:
    if last_update is None:
        raise MtnaRdsError("Cannot patch resource without lastUpdate")
    if isinstance(last_update, datetime):
        iso_value = last_update.isoformat()
        return iso_value.replace("+00:00", "Z")
    if isinstance(last_update, str):
        return last_update
    raise MtnaRdsError("Invalid lastUpdate type for patching")


def _normalize_multilingual_value(field_name: str, value: Any, lang: str) -> list[dict[str, str]]:
    if isinstance(value, str):
        return [{"facetId": lang, "value": value}]

    if isinstance(value, list):
        if _is_valid_facet_list(value):
            return value
        raise MtnaRdsError(f"Invalid multilingual payload for field {field_name}")

    raise MtnaRdsError(f"Invalid multilingual value type for field {field_name}")


def _is_valid_facet_list(value: list[Any]) -> bool:
    if len(value) == 0:
        return False
    for facet in value:
        if not isinstance(facet, dict):
            return False
        if set(facet.keys()) != {"facetId", "value"}:
            return False
        if not isinstance(facet["facetId"], str) or not facet["facetId"]:
            return False
        if not isinstance(facet["value"], str):
            return False
    return True
