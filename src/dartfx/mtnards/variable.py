"""Variable models for MTNA RDS data products."""

from __future__ import annotations

from typing import TYPE_CHECKING

import mlcroissant as mlc
from pydantic import Field, PrivateAttr, computed_field

from .base import MtnaRdsError, MtnaRdsResource

if TYPE_CHECKING:
    from .classification import MtnaRdsClassification, MtnaRdsClassificationStub
    from .data_product import MtnaRdsDataProduct


class MtnaRdsVariableStub(MtnaRdsResource):
    classification_id: str | None = Field(alias="classificationId", default=None)
    classification_uri: str | None = Field(alias="classificationUri", default=None)
    data_type: str | None = Field(alias="dataType", default=None)
    is_dimension: bool | None = Field(alias="isDimension", default=None)
    is_measure: bool | None = Field(alias="isMeasure", default=None)
    is_required: bool | None = Field(alias="isRequired", default=None)
    is_weight: bool | None = Field(alias="isWeight", default=None)
    label: str | None = None
    last_update: str | None = Field(alias="lastUpdate", default=None)
    storage_type: str | None = Field(alias="storageType", default=None)

    # Set by data product @root_validator or programmatically
    _data_product: MtnaRdsDataProduct = PrivateAttr(default=None)  # type: ignore[assignment]

    @property
    def croissant_data_type(self) -> mlc.DataType:
        """Returns the Croissant data type for this variable."""
        if self.data_type == "NUMERIC":
            return mlc.DataType.FLOAT
        return mlc.DataType.TEXT

    @computed_field
    @property
    def catalog_id(self) -> str:
        return self._data_product._catalog.id

    @computed_field
    @property
    def catalog_uri(self) -> str:
        return self._data_product._catalog.uri

    @computed_field
    @property
    def classification(self) -> MtnaRdsClassificationStub | MtnaRdsClassification | None:
        if self.classification_id:
            classification = self._data_product.get_classification_by_id(self.classification_id)
            return classification
        else:
            return None

    @computed_field
    @property
    def data_product_id(self) -> str:
        return self._data_product.id

    @computed_field
    @property
    def data_product_uri(self) -> str:
        return self._data_product.uri

    @computed_field
    @property
    def is_stub(self) -> bool:
        return not isinstance(self, MtnaRdsVariable)

    def resolve(self) -> MtnaRdsVariable:
        """Converts the stub into a detailed variable."""
        url = f"catalog/{self._data_product._catalog.id}/{self._data_product.id}/variable/{self.id}"
        response = self._data_product._catalog._server.api_request(url)
        if response.status_code == 200:
            data = response.json()
            variable = MtnaRdsVariable(**data)
            variable._data_product = self._data_product
            # replace the stub with the detailed variable in the data product
            assert self._data_product._variables is not None
            self._data_product._variables[variable.id] = variable
            return variable
        else:
            raise MtnaRdsError(f"Could not get variable: {response.status_code}")


class MtnaRdsVariable(MtnaRdsVariableStub):
    decimals: int | None = None
    end_position: int | None = Field(alias="endPosition", default=None)
    fixed_storage_width: int | None = Field(alias="fixedStorageWidth", default=None)
    format: str | None = None
    index: int | None = None
    start_position: int | None = Field(alias="startPosition", default=None)

    def resolve(self) -> MtnaRdsVariable:
        """Already resolved — returns self."""
        return self
