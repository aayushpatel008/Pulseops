
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ServerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    hostname: str = Field(..., min_length=1, max_length=255)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    environment: str = Field(default="development", min_length=1, max_length=50)


class ServerUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    hostname: Optional[str] = Field(default=None, min_length=1, max_length=255)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    environment: Optional[str] = Field(default=None, min_length=1, max_length=50)
    status: Optional[str] = Field(default=None, min_length=1, max_length=20)


class ServerResponse(BaseModel):
    id: int
    name: str
    hostname: str
    ip_address: Optional[str]
    environment: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
