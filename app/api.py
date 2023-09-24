from __future__ import annotations

import io
from typing import Any, Dict, Optional, Tuple

from corecrud import Returning, Values, Where
from fastapi import APIRouter, Request
from fastapi.exceptions import HTTPException
from fastapi.param_functions import Body, Depends, Form, Path
from fastapi.responses import StreamingResponse
from likeinterface.exceptions import LikeAPIError
from likeinterface.methods import GetAuthorizationInformationMethod
from magic import Magic, MagicException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from core.crud import crud
from core.depends import get_session
from core.interface import interface
from metadata import MAX_FILE_SIZE
from orm import FileModel
from requests import AddFileRequest, GetFileRequest
from responses import FileResponse
from schema import ApplicationResponse

router = APIRouter()


async def verify_file(
    request: Request,
    file: str = Form(...),
) -> Tuple[bytes, int]:
    form = await request.form()

    file = form.get(file)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="REQUEST_VALIDATION_FAILED",
        )

    if file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="FILE_IS_TOO_BIG",
        )

    upload_file = None

    while content := await file.read(1024):
        if not upload_file:
            upload_file = content
        else:
            upload_file += content

    return upload_file, file.size


async def add_file_core(
    session: AsyncSession,
    request: AddFileRequest,
    file: bytes,
    file_size: int,
) -> FileModel:
    magic = Magic(mime=True)

    try:
        await interface.request(
            method=GetAuthorizationInformationMethod(access_token=request.access_token)
        )
    except LikeAPIError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ACCESS_DENIED",
        )

    try:
        mime_type = request.mime_type or magic.from_buffer(file)
    except MagicException:
        mime_type = "application/octet-stream"

    return await crud.files.insert.one(
        Values(
            {
                FileModel.file: file,
                FileModel.file_name: request.file_name,
                FileModel.file_size: file_size,
                FileModel.mime_type: mime_type,
            }
        ),
        Returning(FileModel),
        session=session,
    )


@router.post(
    path="/addFile",
    response_model=ApplicationResponse[FileResponse],
    status_code=status.HTTP_200_OK,
)
async def add_file(
    file: Tuple[bytes, int] = Depends(verify_file),
    access_token: str = Form(...),
    file_name: Optional[str] = Form(None),
    mime_type: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    upload_file, size = file

    return {
        "ok": True,
        "result": await add_file_core(
            session=session,
            file=upload_file,
            file_size=size,
            request=AddFileRequest(
                access_token=access_token, file_name=file_name, mime_type=mime_type
            ),
        ),
    }


@router.post(
    path="/getFile",
    response_model=ApplicationResponse[FileResponse],
    status_code=status.HTTP_200_OK,
)
async def get_file_information(
    session: AsyncSession = Depends(get_session),
    request: GetFileRequest = Body(...),
) -> Dict[str, Any]:
    file = await crud.files.select.one(
        Where(FileModel.file_id == request.file_id),
        session=session,
    )
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FILE_NOT_EXISTS",
        )

    return {
        "ok": True,
        "result": file,
    }


@router.post(
    path="/file/{file_id}",
    status_code=status.HTTP_200_OK,
)
async def get_file(
    session: AsyncSession = Depends(get_session),
    file_id: str = Path(...),
) -> StreamingResponse:
    file = await crud.files.select.one(
        Where(FileModel.file_id == file_id),
        session=session,
    )
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FILE_NOT_EXISTS",
        )

    return StreamingResponse(
        content=io.BytesIO(file.file),
        media_type=file.mime_type,
    )
