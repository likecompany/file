from __future__ import annotations

import io
from typing import Any, Dict, Optional, Tuple

from corecrud import Returning, Values, Where
from fastapi import APIRouter
from fastapi.datastructures import UploadFile
from fastapi.exceptions import HTTPException
from fastapi.param_functions import Body, Depends, File, Form
from fastapi.responses import StreamingResponse
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from core.crud import crud
from core.depends import get_session
from metadata import MAX_FILE_SIZE
from orm import FileModel
from schema import ApplicationResponse, ApplicationSchema

router = APIRouter()


class FileResponse(ApplicationSchema):
    file_id: str
    file: Optional[bytes] = None
    file_name: Optional[str] = Field(max_length=256)
    file_size: int
    mime_type: Optional[str] = None


class AddFile(ApplicationSchema):
    file_name: Optional[str] = None
    mime_type: Optional[str] = None


class GetFile(ApplicationSchema):
    file_id: str


async def verify_file_size(
    upload_file: UploadFile = File(...),
) -> Tuple[bytes, int, Optional[str], Optional[str]]:
    if upload_file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="FILE_IS_TOO_BIG",
        )

    file = None

    while content := await upload_file.read(1024):
        if not file:
            file = content
        else:
            file += content

    return file, upload_file.size, upload_file.content_type, upload_file.filename


async def add_new_file_core(
    session: AsyncSession,
    file: bytes,
    file_size: int,
    mime_type: Optional[str] = None,
    file_name: Optional[str] = None,
    request: Optional[AddFile] = None,
) -> FileModel:
    if request:
        file_name = request.file_name or file_name
        mime_type = request.mime_type or mime_type

    return await crud.files.insert.one(
        Values(
            {
                FileModel.file: file,
                FileModel.file_name: file_name,
                FileModel.file_size: file_size,
                FileModel.mime_type: mime_type,
            }
        ),
        Returning(FileModel),
        session=session,
    )


@router.post(
    path=".addNewFile",
    response_model=ApplicationResponse[FileResponse],
    response_model_exclude={"result": {"file"}},
    status_code=status.HTTP_200_OK,
)
async def add_new_file(
    file_name: Optional[str] = Form(None),
    mime_type: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_session),
    upload_file: Tuple[bytes, int, Optional[str], Optional[str]] = Depends(verify_file_size),
) -> Dict[str, Any]:
    file, size, upload_mime_type, upload_file_name = upload_file

    return {
        "ok": True,
        "result": await add_new_file_core(
            session=session,
            file=file,
            file_size=size,
            mime_type=upload_mime_type,
            file_name=upload_file_name,
            request=AddFile(file_name=file_name, mime_type=mime_type),
        ),
    }


@router.post(
    path=".getFile",
    status_code=status.HTTP_200_OK,
)
async def get_file(
    session: AsyncSession = Depends(get_session),
    request: GetFile = Body(...),
) -> bytes:
    file = await crud.files.select.one(
        Where(FileModel.file_id == request.file_id),
        session=session,
    )
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="FILE_NOT_EXISTS",
        )

    return StreamingResponse(
        content=io.BytesIO(file.file),
        media_type=file.mime_type,
    )


@router.post(
    path=".getFileInformation",
    response_model=ApplicationResponse[FileResponse],
    response_model_exclude={"result": {"file"}},
    status_code=status.HTTP_200_OK,
)
async def get_file_information(
    session: AsyncSession = Depends(get_session),
    request: GetFile = Body(...),
) -> Dict[str, Any]:
    file = await crud.files.select.one(
        Where(FileModel.file_id == request.file_id),
        session=session,
    )
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="FILE_NOT_EXISTS",
        )

    return {
        "ok": True,
        "result": file,
    }