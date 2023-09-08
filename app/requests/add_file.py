from __future__ import annotations

from typing import Optional

from pydantic import Field

from schema import ApplicationSchema


class AddFileRequest(ApplicationSchema):
    file_name: Optional[str] = Field(None, max_length=256)
    mime_type: Optional[str] = Field(None, max_length=128)
