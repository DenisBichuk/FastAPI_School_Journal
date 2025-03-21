from typing import Annotated

from fastapi import Path, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import db_helper
from . import crud


async def student_by_id(
    student_id: Annotated[int, Path],
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    student = await crud.get_student_by_id(session=session, student_id=student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with id {student_id} not found.",
        )
    return student
