"""Process models for MTNA RDS server operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field, computed_field

if TYPE_CHECKING:
    from .server import MtnaRdsServer


class MtnaRdsProcess(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    server: MtnaRdsServer | None = None
    completed: int
    id: str
    failure: str | None = None
    method_id: str = Field(alias="methodId")
    method_name: str = Field(alias="methodName")
    resource_name: str = Field(alias="resourceName")
    resource_uri: str = Field(alias="resourceUri")
    status: str
    completion_details: Any | None = Field(alias="completionDetails", default=None)

    @computed_field
    @property
    def completed_successfully(self) -> bool:
        return self.completed == 100 and self.status == "COMPLETED"

    @computed_field
    @property
    def failed(self) -> bool:
        return self.completed == 100 and self.status != "COMPLETED"

    @computed_field
    @property
    def in_progress(self) -> bool:
        return self.status == "PROCESSING"

    def __str__(self):
        text = ""
        for attribute, value in vars(self).items():
            if attribute == "server":
                continue
            text += f"{attribute}: {value}\n"
        return text
