"""Classification models for MTNA RDS data products."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import AliasChoices, Field, PrivateAttr, computed_field

from .base import MtnaRdsError, MtnaRdsResource

if TYPE_CHECKING:
    from .data_product import MtnaRdsDataProduct


class MtnaRdsClassificationStub(MtnaRdsResource):
    reference: bool | None = None
    revision_number: int | None = Field(alias="revisionNumber", default=None)
    code_count: int | None = Field(
        serialization_alias="codeCount",
        validation_alias=AliasChoices("codeCount", "rootCodeCount"),
        default=None,
    )

    # Set by data product @root_validator or programmatically
    _data_product: MtnaRdsDataProduct = PrivateAttr(default=None)  # type: ignore[assignment]
    # codes are lazy loaded when the underlying property is accessed
    _codes: list[MtnaRdsClassificationCode] = PrivateAttr(default=None)  # type: ignore[arg-type]

    @computed_field
    @property
    def codes(self) -> list[MtnaRdsClassificationCode]:
        if self._codes is None:
            # get from server
            url = f"catalog/{self._data_product._catalog.id}/{self._data_product.id}/classification/{self.id}/codes"
            response = self._data_product._catalog._server.api_request(url)
            if response.status_code == 200:
                data = response.json()
                self._codes = []
                for item in data:
                    code = MtnaRdsClassificationCode(**item)
                    code._classification = self
                    self._codes.append(code)
            else:
                raise MtnaRdsError(f"Could not get codes for classification {self.id}: {response.status_code}")
        return self._codes

    @computed_field
    @property
    def is_stub(self) -> bool:
        return not isinstance(self, MtnaRdsClassification)

    def resolve(self) -> MtnaRdsClassification:
        """Converts the stub into a detailed classification."""
        url = f"catalog/{self._data_product._catalog.id}/{self._data_product.id}/classification/{self.id}"
        response = self._data_product._catalog._server.api_request(url)
        if response.status_code == 200:
            data = response.json()
            classification = MtnaRdsClassification(**data)
            classification._data_product = self._data_product
            if self._codes:  # transfer the codes if already resolved
                classification._codes = self._codes
                for code in self._codes:
                    code._classification = classification
            assert self._data_product._classifications is not None
            self._data_product._classifications[classification.id] = classification
            return classification
        else:
            raise MtnaRdsError(f"Could not resolve classification {self.id}: {response.status_code}")


class MtnaRdsClassification(MtnaRdsClassificationStub):
    is_private: bool | None = Field(alias="isPrivate", default=None)
    keyword_count: int | None = Field(alias="keywordCount", default=None)
    last_update: str | None = Field(alias="lastUpdate", default=None)
    level_count: int | None = Field(alias="levelCount", default=None)

    def resolve(self) -> MtnaRdsClassification:
        """Already resolved — returns self."""
        return self


class MtnaRdsClassificationCode(MtnaRdsResource):
    id: str | None = None  # type: ignore[assignment]  # override: codes may not have an id
    code_value: str | None = Field(alias="codeValue", default=None)
    is_private: bool | None = Field(alias="isPrivate", default=None)
    reference: bool | None = None

    # Set by classification @root_validator or programmatically
    _classification: MtnaRdsClassificationStub | MtnaRdsClassification = PrivateAttr(default=None)  # type: ignore[assignment]
