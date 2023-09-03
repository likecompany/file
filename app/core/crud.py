from __future__ import annotations

from corecrud import CRUD as CCRUD  # noqa
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from orm import FileModel


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class CRUD:
    files: CCRUD[FileModel] = CCRUD(FileModel)


crud = CRUD()
