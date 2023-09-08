from __future__ import annotations

from typing import Optional

from pydantic import Field

from schema import ApplicationSchema


class FileResponse(ApplicationSchema):
    file_id: str
    file_name: Optional[str] = Field(max_length=256)
    file_size: int
    mime_type: Optional[str] = None
