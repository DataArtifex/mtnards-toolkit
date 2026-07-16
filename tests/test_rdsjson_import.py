import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dartfx.mtnards import MtnaRdsError, import_metadata_rdsjson_workflow
from dartfx.mtnards.catalog import MtnaRdsCatalog
from dartfx.mtnards.data_product import MtnaRdsDataProduct
from dartfx.mtnards.process import MtnaRdsProcess
from dartfx.mtnards.server import MtnaRdsServer


@pytest.fixture
def mock_server() -> MtnaRdsServer:
    return MtnaRdsServer(host="http://localhost", api_key="test-key")


@pytest.fixture
def sample_catalog(mock_server: MtnaRdsServer) -> MtnaRdsCatalog:
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
    return data_product


@patch("requests.request")
def test_get_metadata_rdsjson_config(mock_request, sample_data_product: MtnaRdsDataProduct):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"historyUri": "some-uri", "importProductDocumentation": True}
    mock_request.return_value = mock_response

    result = sample_data_product.get_metadata_rdsjson_config()

    mock_request.assert_called_once()
    call_args = mock_request.call_args
    assert call_args[0][0] == "GET"
    assert "catalog-uri/product/product-uri/metadata/json" in call_args[0][1]
    assert result["importType"] == "DATA_PRODUCT"


@patch("requests.request")
def test_import_metadata_rdsjson_workflow_success(
    mock_request, tmp_path: Path, sample_data_product: MtnaRdsDataProduct
):
    # Create dummy JSON config file
    config_file = tmp_path / "metadata.json"
    config_data = {"metadata": {"dataProduct": {"id": "prod1"}}}
    config_file.write_text(json.dumps(config_data))

    # Mock response for the POST import call
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "process-456", "status": "QUEUED"}
    mock_request.return_value = mock_response

    # Mock server-side process polling response
    mock_process = MagicMock(spec=MtnaRdsProcess)
    mock_process.id = "process-456"
    mock_process.status = "COMPLETED"

    with patch("dartfx.mtnards.server.MtnaRdsServer.wait_for_process", return_value=mock_process) as mock_wait:
        result = import_metadata_rdsjson_workflow(sample_data_product, config_file)

        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert "catalog-uri/product/product-uri/import" in call_args[0][1]

        # Verify importType was injected in JSON body
        assert call_args[1]["json"]["importType"] == "DATA_PRODUCT"

        mock_wait.assert_called_once_with("process-456")
        assert result == mock_process


def test_import_metadata_rdsjson_workflow_file_not_found(sample_data_product: MtnaRdsDataProduct):
    with pytest.raises(FileNotFoundError):
        import_metadata_rdsjson_workflow(sample_data_product, "nonexistent.json")


def test_import_metadata_rdsjson_workflow_parse_error(tmp_path: Path, sample_data_product: MtnaRdsDataProduct):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{bad json}")

    with pytest.raises(MtnaRdsError) as exc_info:
        import_metadata_rdsjson_workflow(sample_data_product, bad_file)
    assert "Failed to read/parse native RDS JSON file" in str(exc_info.value)
