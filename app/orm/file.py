from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from .core import ORMModel, types


def file_id_default() -> str:
    return uuid.uuid4().hex


class FileModel(ORMModel):
    file_id: Mapped[types.Text] = mapped_column(default=file_id_default, primary_key=True)
    file: Mapped[bytes]
    file_name: Mapped[Optional[types.String256]]
    file_size: Mapped[types.BigInt]
    mime_type: Mapped[types.Text]
