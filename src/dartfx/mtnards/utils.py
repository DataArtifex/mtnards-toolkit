"""Utility functions for MTNA RDS resource management."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .base import MtnaRdsError

if TYPE_CHECKING:
    from .data_product import MtnaRdsDataProduct
    from .server import MtnaRdsProcess


def import_ddic_metadata(
    data_product: MtnaRdsDataProduct,
    xml_path: str | Path,
) -> MtnaRdsProcess:
    """Uploads and applies a DDI-C XML document to a data product.

    This helper automates the multi-step process of uploading the file to the
    server's temporary files endpoint, retrieving the import configuration for
    the uploaded file, executing the import process, and polling/waiting for the
    import job to complete on the server.

    Args:
        data_product: The target data product to apply the metadata to.
        xml_path: The filesystem path to the DDI Codebook XML file.

    Returns:
        MtnaRdsProcess: The completed server-side process details.

    Raises:
        MtnaRdsError: If the upload, configuration retrieval, import, or wait
            operation fails.
        FileNotFoundError: If the DDI XML file does not exist.
    """
    path_obj = Path(xml_path)
    if not path_obj.is_file():
        raise FileNotFoundError(f"DDI XML file not found at: {path_obj}")

    catalog = data_product._catalog
    if catalog is None:
        raise MtnaRdsError("Data product is not attached to a catalog")

    server = catalog._server
    if server is None:
        raise MtnaRdsError("Catalog is not attached to a server")

    # 1. Upload the XML file to the server's temporary files space
    try:
        file_info = server.upload_file(path_obj)
    except Exception as e:
        raise MtnaRdsError(f"Failed to upload DDI XML file: {e}") from e

    # 2. Get import configuration for the product
    try:
        import_config = data_product.get_import_configuration(file_info)
    except Exception as e:
        raise MtnaRdsError(f"Failed to retrieve import configuration: {e}") from e

    # 3. Start the import file job on the server
    try:
        process_info = server.import_file(
            catalog_uri=catalog.uri,
            product_uri=data_product.uri,
            import_configuration=import_config,
        )
    except Exception as e:
        raise MtnaRdsError(f"Failed to trigger DDI XML metadata import: {e}") from e

    pid = process_info.get("id")
    if not pid:
        raise MtnaRdsError("Server did not return a valid process ID for the import")

    # 4. Wait for the server-side process to complete
    try:
        completed_process = server.wait_for_process(pid)
        return completed_process
    except Exception as e:
        raise MtnaRdsError(f"Error occurred while waiting for import process {pid} to complete: {e}") from e


def import_metadata_rdsjson_workflow(
    data_product: MtnaRdsDataProduct,
    json_path: str | Path,
) -> MtnaRdsProcess:
    """Uploads and applies native RDS JSON metadata to a data product.

    This helper automates reading the local RDS JSON metadata file, submitting
    the configuration JSON payload directly to the server's import endpoint,
    and polling/waiting for the server-side process to complete.

    Args:
        data_product: The target data product to apply the metadata to.
        json_path: The filesystem path to the native RDS JSON metadata file.

    Returns:
        MtnaRdsProcess: The completed server-side process details.

    Raises:
        MtnaRdsError: If the import trigger or process waiting fails.
        FileNotFoundError: If the JSON file does not exist.
    """
    import json

    path_obj = Path(json_path)
    if not path_obj.is_file():
        raise FileNotFoundError(f"JSON metadata file not found at: {path_obj}")

    try:
        with path_obj.open("r", encoding="utf-8") as f:
            config_data = json.load(f)
    except Exception as e:
        raise MtnaRdsError(f"Failed to read/parse native RDS JSON file: {e}") from e

    catalog = data_product._catalog
    if catalog is None:
        raise MtnaRdsError("Data product is not attached to a catalog")

    server = catalog._server
    if server is None:
        raise MtnaRdsError("Catalog is not attached to a server")

    # 1. Start the import metadata job on the server
    try:
        process_info = data_product.import_metadata_rdsjson(config_data)
    except Exception as e:
        raise MtnaRdsError(f"Failed to trigger native RDS JSON metadata import: {e}") from e

    pid = process_info.get("id")
    if not pid:
        raise MtnaRdsError("Server did not return a valid process ID for the import")

    # 2. Wait for the server-side process to complete
    try:
        completed_process = server.wait_for_process(pid)
        return completed_process
    except Exception as e:
        raise MtnaRdsError(f"Error occurred while waiting for import process {pid} to complete: {e}") from e
