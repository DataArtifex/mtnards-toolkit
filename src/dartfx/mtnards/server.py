"""Server model for MTNA RDS connections."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import requests
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, computed_field, model_validator

from .base import MtnaRdsError, MtnaRdsServerInfo
from .process import MtnaRdsProcess

if TYPE_CHECKING:
    from .catalog import MtnaRdsCatalog


class MtnaRdsServer(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    host: str
    base_path: str | None = Field(default="rds")
    api_path: str | None = Field(default="api")
    api_key: str | None = None
    ssl_verify: bool = Field(default=True)
    _catalogs: dict[str, MtnaRdsCatalog] | None = PrivateAttr(default=None)
    _info: MtnaRdsServerInfo | None = PrivateAttr(default=None)

    # This validator ensures that the host URL starts with "https://" before model initialization.
    @model_validator(mode="before")
    @classmethod
    def ensure_https_host(cls, values):
        host = values.get("host")
        if host and not re.match(r"^https?://", host):
            values["host"] = f"https://{host}"
        return values

    @computed_field
    @property
    def api_endpoint(self) -> str:
        base = self.base_path or ""
        api = self.api_path or ""
        return f"{base}/{api}" if base else api

    @property
    def catalogs(self) -> dict[str, MtnaRdsCatalog]:
        """Returns the server's catalogs, loading them on first access."""
        if self._catalogs is None:
            self._load_catalogs()
        assert self._catalogs is not None  # set by _load_catalogs or raises
        return self._catalogs

    def refresh_catalogs(self) -> dict[str, MtnaRdsCatalog]:
        """Refreshes and returns the catalog list from the server."""
        self._catalogs = None
        return self.catalogs

    def _load_catalogs(self) -> None:
        """Loads catalogs from the server API."""
        from .catalog import MtnaRdsCatalog

        response = self.api_request("catalog")
        if response.status_code == 200:
            data = response.json()
            self._catalogs = {}
            for item in data["catalogs"]:
                catalog = MtnaRdsCatalog(**item)
                catalog._server = self
                self._catalogs[catalog.id] = catalog
        else:
            raise MtnaRdsError(f"Could not get server level catalog: {response.status_code}")

    @computed_field
    @property
    def base_url(self) -> str:
        return f"{self.host}/{self.base_path}"

    @computed_field
    @property
    def api_url(self) -> str:
        return f"{self.host}/{self.api_endpoint}"

    @computed_field
    @property
    def hostname(self) -> str:
        return re.sub(r"^https?://", "", self.host)

    @computed_field
    @property
    def info(self) -> MtnaRdsServerInfo:
        if self._info is None:
            response = self.api_request("server/info")
            if response.status_code == 200:
                data = response.json()
                self._info = MtnaRdsServerInfo(**data)
            else:
                raise MtnaRdsError(f"Could not get server info: {response.status_code}")
        return self._info

    @computed_field
    @property
    def explorer_url(self) -> str:
        return f"{self.host}/{self.base_path}/explorer"

    @computed_field
    @property
    def tabengine_url(self) -> str:
        return f"{self.host}/{self.base_path}/tabengine"

    def api_request(
        self,
        path: str,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        body_json: dict[str, Any] | None = None,
    ) -> requests.Response:
        """Makes an HTTP request to this server's API."""
        if headers is None:
            headers = {}
        if "X-API-KEY" not in headers and self.api_key:
            headers["X-API-KEY"] = self.api_key
        url = f"{self.api_url}/{path}"
        response = requests.request(method, url, headers=headers, params=params, json=body_json, verify=self.ssl_verify)
        return response

    def create_catalog(
        self,
        id: str,
        name: str | None = None,
        description: str | None = None,
        is_private: bool = True,
        lang: str = "en",
    ) -> Any:
        """Creates a new catalog on the server."""
        body = {
            "id": id,
            "name": [{"facetId": lang, "value": name}],
            "description": [{"facetId": lang, "value": description}],
            "isPrivate": is_private,
        }
        response = self.api_request("management/catalog", method="POST", body_json=body)
        if response.status_code == 200:
            process_id = response.json()
            return process_id
        else:
            raise MtnaRdsError(f"Could not create catalog: {response.status_code}")

    def delete_catalog(self, id: str) -> Any:
        """Deletes a catalog by ID."""
        response = self.api_request(f"management/catalog/{id}", method="DELETE")
        if response.status_code == 200:
            process_id = response.json()
            return process_id
        else:
            raise MtnaRdsError(f"Could not delete catalog: {response.status_code}")

    def delete_data_product(self, catalog_uri: str, data_product_uri: str) -> Any:
        """Deletes a data product from a catalog."""
        path = f"management/catalog/{catalog_uri}/product/{data_product_uri}"
        result = self.api_request(path, method="DELETE")
        if result.status_code == 200:
            return result.json()
        else:
            raise MtnaRdsError(f"Could not delete data product: {result.status_code}")

    def get_catalog_by_uri(self, uri: str) -> MtnaRdsCatalog | None:
        """Returns a catalog by its URI, or ``None`` if not found."""
        for catalog in self.catalogs.values():
            if catalog.uri == uri:
                return catalog
        return None

    def get_catalog_by_id(self, id: str) -> MtnaRdsCatalog | None:
        """Returns a catalog by its ID, or ``None`` if not found."""
        return self.catalogs.get(id)

    def get_ddi_codebook(
        self,
        catalog_id: str,
        product_id: str,
        include_variables: bool = True,
        include_statistics: bool = False,
    ) -> bytes:
        """Returns the DDI Codebook XML for a data product."""
        path = f"catalog/{catalog_id}/{product_id}/ddi-codebook"
        params = {
            "includeVariables": include_variables,
            "includeStatistics": include_statistics,
        }
        response = self.api_request(path, params=params)
        if response.status_code == 200:
            return response.content
        else:
            raise MtnaRdsError(f"Could not retrieve DDI-Codebook: {response.status_code} {path}")

    def get_import_configuration(self, catalog_uri: str, product_uri: str, file_info: dict[str, Any]) -> dict[str, Any]:
        """Returns import configuration for a data product."""
        path = f"management/catalog/{catalog_uri}/product/{product_uri}/import/configure"
        response = self.api_request(path, method="POST", body_json=file_info)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            raise MtnaRdsError(f"Could not get import configuration: {response.status_code}")

    def get_info(self) -> dict[str, Any]:
        """Returns server information as a dictionary."""
        path = "server/info"
        response = self.api_request(path)
        if response.status_code == 200:
            return response.json()
        else:
            raise MtnaRdsError(f"Could not get server info: {response.status_code}")

    def get_postman_collection(
        self, catalog_id: str | None = None, data_product_id: str | None = None
    ) -> dict[str, Any]:
        """Returns a Postman collection for the server, a catalog, or a data product."""
        url = "management/postman"
        if catalog_id:
            url += f"/{catalog_id}"
            if data_product_id:
                url += f"/{data_product_id}"
        params = {
            "rdsBaseUrl": self.base_url,
            "rdsExplorerBaseUrl": f"{self.base_url}/explorer/explore",
            "rdsTabEngineBaseUrl": f"{self.base_url}/tabengine/tabulation",
        }
        result = self.api_request(url, method="GET", params=params)
        if result.status_code == 200:
            data = result.json()
            # patch
            del data["info"]["_postman_id"]  # remove to prevent an invalidUidError
            return data
        else:
            raise MtnaRdsError(f"Could not retrieve Postman collection: {result.status_code}")

    def get_process_details(self, process_id: str) -> MtnaRdsProcess:
        """Returns details of a server-side process."""
        path = f"management/catalog/process/details/{process_id}"
        response = self.api_request(path)
        if response.status_code == 200:
            data = response.json()
            process = MtnaRdsProcess(server=self, **data)
            return process
        else:
            raise MtnaRdsError(f"Could not get process details: {response.status_code}")

    def import_file(self, catalog_uri: str, product_uri: str, import_configuration: dict[str, Any]) -> Any:
        """Imports data into a data product."""
        path = f"management/catalog/{catalog_uri}/product/{product_uri}/import"
        response = self.api_request(path, method="POST", body_json=import_configuration)
        if response.status_code == 200:
            return response.json()
        else:
            raise MtnaRdsError(f"Could not import: {response.status_code}")

    def is_up(self) -> bool:
        """Returns ``True`` if the server is reachable, ``False`` otherwise."""
        try:
            return self.get_info() is not None
        except (MtnaRdsError, requests.RequestException):
            return False

    def upload_file(self, filepath: str | Path) -> dict[str, Any]:
        """Uploads a file to the server."""
        url = f"{self.base_url}/_files/upload"
        filepath = Path(filepath)
        if not filepath.is_file():
            raise FileNotFoundError(f"File not found: {filepath}")
        with filepath.open("rb") as f:
            files = {"file": f}
            response = requests.post(url, files=files, headers={"X-API-KEY": self.api_key}, verify=self.ssl_verify)
            if response.status_code == 200:
                return response.json()
            else:
                raise MtnaRdsError(f"Could not upload file: {response.status_code}")

    def wait_for_process(
        self, pid: str, sleep: int = 1, timeout: int = 60 * 5, max_get_errors: int = 10
    ) -> MtnaRdsProcess:
        """Waits for a server-side process to complete."""
        start = time.time()
        get_errors = 0
        process_details = None
        while time.time() - start < timeout:
            try:
                process_details = self.get_process_details(pid)
                if process_details.completed == 100:
                    break
            except MtnaRdsError:
                get_errors += 1
                if get_errors > max_get_errors:
                    raise MtnaRdsError(
                        f"Retrieving process {pid} details failed too many times ({get_errors})"
                    ) from None
            time.sleep(sleep)
        if process_details is None:
            raise MtnaRdsError(f"Timed out waiting for process {pid} after {timeout}s")
        return process_details
