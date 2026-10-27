from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


IncidentStatus = Literal["open", "in_progress", "resolved"]
IncidentPriority = Literal["low", "medium", "high"]


class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=1000)
    priority: IncidentPriority = "medium"


class IncidentUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=200,
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
    )
    status: IncidentStatus | None = None
    priority: IncidentPriority | None = None


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: str
    priority: str