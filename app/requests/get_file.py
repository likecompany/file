from __future__ import annotations

from schema import ApplicationSchema


class GetFileRequest(ApplicationSchema):
    file_id: str
