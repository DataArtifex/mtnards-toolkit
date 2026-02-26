"""Catalog model for MTNA RDS catalogs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field, PrivateAttr, model_validator

from .base import MtnaRdsError, MtnaRdsResource

if TYPE_CHECKING:
    from .data_product import MtnaRdsDataProduct
    from .server import MtnaRdsServer


class MtnaRdsCatalog(MtnaRdsResource):
    last_update: str = Field(alias="lastUpdate")
    is_private: bool = Field(alias="isPrivate")
    data_products: list[MtnaRdsDataProduct] | None = Field(alias="dataProducts", default=None)

    # Set by server @root_validator or programmatically
    _server: MtnaRdsServer = PrivateAttr(default=None)

    @model_validator(mode="after")
    def attach_catalog_to_products(self):
        # attach the catalog to the data products
        if self.data_products:
            for product in self.data_products:
                product._catalog = self
        return self

    def __str__(self) -> str:
        text = ""
        if self._server:
            text += f"server uri: {self._server.host}\n"
        for attribute, value in self.model_dump(exclude={"data_products"}).items():
            text += f"{attribute}: {value}\n"
        if self.data_products:
            text += f"#data_products: {len(self.data_products)}\n"
        return text

    def get_data_product_by_uri(self, uri: str) -> MtnaRdsDataProduct | None:
        """Returns a data product by its URI, or ``None`` if not found."""
        if not self.data_products:
            return None
        for product in self.data_products:
            if product.uri == uri:
                return product
        return None

    def get_data_product_by_id(self, id: str) -> MtnaRdsDataProduct | None:
        """Returns a data product by its ID, or ``None`` if not found."""
        if not self.data_products:
            return None
        for product in self.data_products:
            if product.id == id:
                return product
        return None

    @property
    def data_products_by_id(self) -> dict[str, MtnaRdsDataProduct]:
        """Returns data products indexed by their id."""
        if self.data_products is None:
            return {}
        return {product.id: product for product in self.data_products}

    def get_ddi_codebook(
        self,
        product_id: str,
        include_variables: bool = True,
        include_statistics: bool = False,
    ) -> bytes:
        """Returns the DDI Codebook XML for a data product in this catalog."""
        return self._server.get_ddi_codebook(self.id, product_id, include_variables, include_statistics)

    def get_import_configuration(self, product_uri: str, file_info: dict[str, Any]) -> dict[str, Any]:
        """Returns import configuration for a data product."""
        return self._server.get_import_configuration(self.uri, product_uri, file_info)

    def create_sql_data_product(
        self,
        id: str,
        connection_string: str,
        table_name: str,
        username: str,
        password: str,
        name: str | None = None,
        description: str | None = None,
        is_private: bool = True,
        lang: str = "en",
    ) -> Any:
        """Creates a SQL-backed data product in this catalog."""
        if not name:
            name = id
        body = {
            "dataSource": {
                "id": id,
                "configuration": {
                    "$type": "SQL",
                    "tableName": table_name,
                    "connectionString": connection_string,
                    "user": username,
                    "password": password,
                },
            },
            "description": [{"facetId": lang, "value": description}],
            "id": id,
            "isPrivate": is_private,
            "name": [{"facetId": lang, "value": name}],
        }
        url = f"management/catalog/{self.uri}/product"
        result = self._server.api_request(url, method="POST", body_json=body)
        if result.status_code == 200:
            return result.json()
        else:
            raise MtnaRdsError(f"Could not create data product: {result.status_code}")

    def delete(self) -> Any:
        """Deletes this catalog from the server."""
        return self._server.delete_catalog(self.uri)

    def delete_data_product(self, data_product_uri: str) -> Any:
        """Deletes a data product from this catalog."""
        return self._server.delete_data_product(self.uri, data_product_uri)

    def get_postman_collection(self, data_product_id: str | None = None) -> dict[str, Any]:
        """Returns a Postman collection for this catalog or one of its data product."""
        return self._server.get_postman_collection(self.id, data_product_id)
