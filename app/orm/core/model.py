from __future__ import annotations

from typing import cast

import stringcase
from sqlalchemy.orm import DeclarativeBase, declared_attr


class ORMModel(DeclarativeBase):
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:  # noqa
        return cast(str, stringcase.snakecase(cls.__name__.split("Model")[0]))
