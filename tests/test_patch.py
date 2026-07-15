from typing import cast
from unittest.mock import MagicMock

import pytest

from dartfx.mtnards.base import MtnaRdsError, MtnaRdsPatchConflictError
from dartfx.mtnards.catalog import MtnaRdsCatalog
from dartfx.mtnards.data_product import MtnaRdsDataProduct
from dartfx.mtnards.patching import build_patch_request, refresh_resource_from_server, sync_resource_from_payload
from dartfx.mtnards.variable import MtnaRdsVariableStub


@pytest.fixture
def mock_server() -> MagicMock:
    return MagicMock()


@pytest.fixture
def sample_catalog(mock_server: MagicMock) -> MtnaRdsCatalog:
    catalog = MtnaRdsCatalog(
        id="cat1",
        uri="catalog-uri",
        name="Catalog Name",
        lastUpdate="2026-04-14T16:41:59.64Z",
        isPrivate=False,
        data_products=[],
    )
    catalog._server = mock_server
    return catalog


@pytest.fixture
def sample_data_product(sample_catalog: MtnaRdsCatalog) -> MtnaRdsDataProduct:
    data_product = MtnaRdsDataProduct(
        id="prod1",
        uri="product-uri",
        name="Product Name",
        lastUpdate="2026-04-14T16:41:59.64Z",
        isPrivate=False,
    )
    data_product._catalog = sample_catalog
    sample_catalog.data_products = [data_product]
    return data_product


@pytest.fixture
def sample_variable(sample_data_product: MtnaRdsDataProduct) -> MtnaRdsVariableStub:
    variable = MtnaRdsVariableStub(
        id="V1",
        uri="variable-uri",
        name="var_name",
        label="Old label",
        classificationUri="classification-uri",
        classificationId="CLS1",
        isMeasure=True,
        lastUpdate="2026-04-14T16:41:59.64Z",
    )
    variable._data_product = sample_data_product
    return variable


def test_build_patch_request_variable_normalizes_label(sample_variable: MtnaRdsVariableStub) -> None:
    request = build_patch_request(sample_variable, {"label": "EDUCATION OF RESPONDENT", "is_measure": False})

    assert request.path == "management/variable/variable-uri"
    assert request.payload["lastUpdate"] == "2026-04-14T16:41:59.64Z"
    assert request.payload["uri"] == "variable-uri"
    assert request.payload["label"] == [{"facetId": "en", "value": "EDUCATION OF RESPONDENT"}]
    assert request.payload["isMeasure"] is False


def test_build_patch_request_rejects_non_patchable_fields(sample_variable: MtnaRdsVariableStub) -> None:
    with pytest.raises(MtnaRdsError, match="Field is not patchable"):
        build_patch_request(sample_variable, {"uri": "new-uri"})

    with pytest.raises(MtnaRdsError, match="Field is not patchable"):
        build_patch_request(sample_variable, {"lastUpdate": "2026-01-01T00:00:00Z"})

    with pytest.raises(MtnaRdsError, match="Field is not patchable"):
        build_patch_request(sample_variable, {"id": "V2"})


def test_build_patch_request_rejects_catalog_id(sample_catalog: MtnaRdsCatalog) -> None:
    with pytest.raises(MtnaRdsError, match="Field is not patchable"):
        build_patch_request(sample_catalog, {"id": "cat2"})


def test_build_patch_request_rejects_data_product_id(sample_data_product: MtnaRdsDataProduct) -> None:
    with pytest.raises(MtnaRdsError, match="Field is not patchable"):
        build_patch_request(sample_data_product, {"id": "prod2"})


def test_build_patch_request_passes_through_valid_facets(sample_variable: MtnaRdsVariableStub) -> None:
    facets = [{"facetId": "en", "value": "EDUCATION"}]
    request = build_patch_request(sample_variable, {"label": facets})
    assert request.payload["label"] == facets


def test_build_patch_request_rejects_invalid_facets(sample_variable: MtnaRdsVariableStub) -> None:
    with pytest.raises(MtnaRdsError, match="Invalid multilingual payload"):
        build_patch_request(sample_variable, {"label": [{"value": "missing facet"}]})


def test_catalog_patch_syncs_from_response(sample_catalog: MtnaRdsCatalog, mock_server: MagicMock) -> None:
    mock_server.patch_management.return_value = {
        "id": "cat1",
        "uri": "catalog-uri",
        "name": [{"facetId": "en", "value": "Updated Catalog Name"}],
        "isPrivate": True,
        "lastUpdate": "2026-04-23T10:00:00Z",
        "dataProducts": [],
    }

    sample_catalog.patch({"name": "Updated Catalog Name"})

    assert sample_catalog.name == "Updated Catalog Name"
    assert sample_catalog.last_update == "2026-04-23T10:00:00Z"
    mock_server.patch_management.assert_called_once()
    call = mock_server.patch_management.call_args
    assert call.args[0] == "management/catalog/catalog-uri"
    assert call.args[1]["uri"] == "catalog-uri"


def test_catalog_patch_prefers_refreshed_resource_state(
    sample_catalog: MtnaRdsCatalog,
    mock_server: MagicMock,
) -> None:
    """Catalog patch should prefer the refreshed GET result over the PATCH payload."""
    mock_server.patch_management.return_value = {
        "id": "cat1",
        "uri": "catalog-uri",
        "name": [{"facetId": "en", "value": "Updated Catalog Name"}],
        "isPrivate": True,
        "lastUpdate": "2026-04-23T10:00:00Z",
        "dataProducts": [],
    }

    refreshed_catalog = MtnaRdsCatalog(
        id="cat1",
        uri="catalog-uri",
        name="Updated Catalog Name",
        lastUpdate="2026-04-23T10:00:00Z",
        isPrivate=True,
        data_products=[
            MtnaRdsDataProduct(
                id="anes1948",
                uri="product-uri",
                name="ANES 1948 Time Series Study",
                description="Election survey.",
                abbreviation="ANES1948",
                lastUpdate="2026-04-23T09:59:59Z",
                isPrivate=False,
            )
        ],
    )
    refreshed_catalog._server = mock_server
    for product in refreshed_catalog.data_products or []:
        product._catalog = refreshed_catalog

    mock_server.get_catalog_by_uri.return_value = MagicMock(id="cat1")
    mock_server.get_catalog_by_id.return_value = refreshed_catalog

    sample_catalog.patch({"name": "Updated Catalog Name"})

    assert sample_catalog.data_products is not None
    assert len(sample_catalog.data_products) == 1
    product = sample_catalog.data_products[0]
    assert product.name == "ANES 1948 Time Series Study"
    assert product.description == "Election survey."
    assert product.abbreviation == "ANES1948"


def test_catalog_patch_on_conflict_refreshes_and_raises(
    sample_catalog: MtnaRdsCatalog,
    mock_server: MagicMock,
) -> None:
    conflict = MtnaRdsPatchConflictError("catalog", "catalog-uri", {"name": "New"})
    mock_server.patch_management.side_effect = conflict

    refreshed = MtnaRdsCatalog(
        id="cat1",
        uri="catalog-uri",
        name="Server Name",
        lastUpdate="2026-04-23T11:00:00Z",
        isPrivate=False,
        data_products=[],
    )
    refreshed._server = mock_server
    mock_server.get_catalog_by_id.return_value = refreshed

    with pytest.raises(MtnaRdsPatchConflictError) as exc:
        sample_catalog.patch({"name": "New"})

    assert exc.value.refreshed_resource is refreshed
    mock_server.get_catalog_by_id.assert_called_once_with("cat1", fetch=True)


def test_variable_patch_resolves_stub_when_last_update_missing(sample_data_product: MtnaRdsDataProduct) -> None:
    """Variable patch should resolve a stub first when lastUpdate is missing."""
    server = cast(MagicMock, sample_data_product._catalog._server)

    variable = MtnaRdsVariableStub(
        id="V1",
        uri="variable-uri",
        name="var_name",
        label="Old label",
        isMeasure=True,
    )
    variable._data_product = sample_data_product
    sample_data_product._variables = {variable.id: variable}

    resolve_response = MagicMock()
    resolve_response.status_code = 200
    resolve_response.json.return_value = {
        "id": "V1",
        "uri": "variable-uri",
        "name": "var_name",
        "label": "Old label",
        "isMeasure": True,
        "lastUpdate": "2026-04-23T10:00:00Z",
    }

    server.api_request.return_value = resolve_response
    server.patch_management.return_value = {
        "id": "V1",
        "uri": "variable-uri",
        "name": "var_name",
        "label": [{"facetId": "en", "value": "Updated label"}],
        "isMeasure": True,
        "lastUpdate": "2026-04-23T10:01:00Z",
    }

    patched = variable.patch({"label": "Updated label"})

    assert patched.label == "Updated label"
    assert patched.last_update == "2026-04-23T10:01:00Z"
    server.api_request.assert_called_once_with("catalog/cat1/prod1/variable/V1")
    server.patch_management.assert_called_once()
    patch_call = server.patch_management.call_args
    assert patch_call.args[0] == "management/variable/variable-uri"
    assert patch_call.args[1]["lastUpdate"] == "2026-04-23T10:00:00Z"


def test_sync_resource_from_payload_normalizes_faceted_label(sample_variable: MtnaRdsVariableStub) -> None:
    """Sync should convert faceted multilingual payloads into plain strings."""
    payload = {
        "id": "V1",
        "uri": "variable-uri",
        "name": "var_name",
        "label": [{"facetId": "en", "value": "Normalized Label"}],
        "isMeasure": True,
        "lastUpdate": "2026-04-23T10:03:00Z",
    }

    sync_resource_from_payload(sample_variable, payload)

    assert sample_variable.label == "Normalized Label"


def test_sync_resource_from_payload_preserves_classification_when_omitted(
    sample_variable: MtnaRdsVariableStub,
) -> None:
    """Sync should retain existing classification fields if PATCH response omits them."""
    payload = {
        "id": "V1",
        "uri": "variable-uri",
        "name": "var_name",
        "label": [{"facetId": "en", "value": "Updated Label"}],
        "isMeasure": True,
        "lastUpdate": "2026-04-23T10:04:00Z",
    }

    sync_resource_from_payload(sample_variable, payload)

    assert sample_variable.classification_id == "CLS1"
    assert sample_variable.classification_uri == "classification-uri"
    assert sample_variable.label == "Updated Label"


def test_refresh_resource_from_server_variable_prefers_uri(sample_variable: MtnaRdsVariableStub) -> None:
    """Conflict refresh should resolve variable via URI-first lookup chain."""
    server = cast(MagicMock, sample_variable._data_product._catalog._server)

    refreshed_catalog = MagicMock()
    refreshed_catalog.id = "cat1"
    refreshed_product = MagicMock()
    refreshed_variable = MagicMock()

    server.refresh_catalogs = MagicMock()
    server.get_catalog_by_uri.return_value = refreshed_catalog
    server.get_catalog_by_id.return_value = refreshed_catalog
    refreshed_catalog.get_data_product_by_uri.return_value = refreshed_product
    refreshed_product.get_variable_by_uri.return_value = refreshed_variable

    result = refresh_resource_from_server(sample_variable)

    server.refresh_catalogs.assert_called_once_with()
    server.get_catalog_by_uri.assert_called_once_with("catalog-uri")
    refreshed_catalog.get_data_product_by_uri.assert_called_once_with("product-uri")
    refreshed_product.get_variable_by_uri.assert_called_once_with("variable-uri")
    assert result is refreshed_variable
