from pathlib import Path
from unittest.mock import MagicMock

import pytest

from dartfx.mtnards import MtnaRdsError, import_ddic_metadata
from dartfx.mtnards.catalog import MtnaRdsCatalog
from dartfx.mtnards.data_product import MtnaRdsDataProduct
from dartfx.mtnards.process import MtnaRdsProcess


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
    return data_product


def test_import_ddic_metadata_success(tmp_path: Path, sample_data_product: MtnaRdsDataProduct, mock_server: MagicMock):
    # Create a dummy XML file
    xml_file = tmp_path / "metadata.xml"
    xml_file.write_text("<codebook />")

    # Mock server calls
    file_info = {"path": "temp/metadata.xml", "size": 12, "originalName": "metadata.xml"}
    mock_server.upload_file.return_value = file_info

    import_config = {"configuration": "options"}
    mock_server.get_import_configuration.return_value = import_config

    process_info = {"id": "process-123", "status": "QUEUED"}
    mock_server.import_file.return_value = process_info

    mock_process = MagicMock(spec=MtnaRdsProcess)
    mock_process.id = "process-123"
    mock_process.status = "COMPLETED"
    mock_server.wait_for_process.return_value = mock_process

    # Run the utility workflow
    result = import_ddic_metadata(sample_data_product, xml_file)

    # Verify calls
    mock_server.upload_file.assert_called_once_with(xml_file)
    mock_server.get_import_configuration.assert_called_once_with(
        sample_data_product.catalog_uri, sample_data_product.uri, file_info
    )
    mock_server.import_file.assert_called_once_with(
        catalog_uri=sample_data_product.catalog_uri,
        product_uri=sample_data_product.uri,
        import_configuration=import_config,
    )
    mock_server.wait_for_process.assert_called_once_with("process-123")
    assert result == mock_process


def test_import_ddic_metadata_file_not_found(sample_data_product: MtnaRdsDataProduct):
    with pytest.raises(FileNotFoundError):
        import_ddic_metadata(sample_data_product, "nonexistent_file.xml")


def test_import_ddic_metadata_upload_failure(
    tmp_path: Path, sample_data_product: MtnaRdsDataProduct, mock_server: MagicMock
):
    xml_file = tmp_path / "metadata.xml"
    xml_file.write_text("<codebook />")

    mock_server.upload_file.side_effect = Exception("Upload timed out")

    with pytest.raises(MtnaRdsError) as exc_info:
        import_ddic_metadata(sample_data_product, xml_file)
    assert "Failed to upload DDI XML file" in str(exc_info.value)
