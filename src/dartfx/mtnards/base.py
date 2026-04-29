"""Base classes and exceptions for MTNA RDS models."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MtnaRdsError(Exception):
    """Exception raised when an MTNA RDS API operation fails."""


class MtnaRdsPatchConflictError(MtnaRdsError):
    """Conflict raised when patching with an outdated lastUpdate token."""

    def __init__(
        self,
        resource_kind: str,
        resource_uri: str,
        attempted_updates: dict[str, Any] | None = None,
        message: str | None = None,
    ) -> None:
        if message is None:
            message = f"Patch conflict for {resource_kind} {resource_uri} (HTTP 409)"
        super().__init__(message)
        self.resource_kind = resource_kind
        self.resource_uri = resource_uri
        self.attempted_updates = attempted_updates or {}
        self.refreshed_resource: Any | None = None


class MtnaRdsResource(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    uri: str
    id: str
    name: str | None = None
    description: str | None = None
    reference: bool | None = None
    revision_number: int | None = Field(alias="revisionNumber", default=None)
    last_update: str | None = Field(alias="lastUpdate", default=None)

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
