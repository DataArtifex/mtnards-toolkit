"""Base classes and exceptions for MTNA RDS models."""

from pydantic import BaseModel, ConfigDict, Field


class MtnaRdsError(Exception):
    """Exception raised when an MTNA RDS API operation fails."""


class MtnaRdsResource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    uri: str
    id: str
    name: str | None = None
    description: str | None = None
    reference: bool | None = None
    revision_number: int | None = Field(alias="revisionNumber", default=None)

    def __eq__(self, other: object) -> bool:
        """Two resources are equal if they share the same URI."""
        if not isinstance(other, MtnaRdsResource):
            return NotImplemented
        return self.uri == other.uri

    def __hash__(self) -> int:
        """Make the object hashable by using the uri so it can be used in sets."""
        return hash(self.uri)


class MtnaRdsServerInfo(BaseModel):
    name: str
    released: str
    version: str
