from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.school import Board, School, SchoolModerator
from app.models.user import User


async def moderated_school_ids(db: AsyncSession, user: User) -> set[int]:
    if user.is_admin:
        result = await db.execute(select(School.id).where(School.is_active == True))  # noqa: E712
        return set(result.scalars().all())
    result = await db.execute(
        select(SchoolModerator.school_id).where(
            SchoolModerator.user_id == user.id,
            SchoolModerator.is_active == True,  # noqa: E712
        )
    )
    return set(result.scalars().all())


async def can_manage_school(db: AsyncSession, user: User, school_id: int) -> bool:
    if user.is_admin:
        return True
    result = await db.execute(
        select(SchoolModerator.id).where(
            SchoolModerator.user_id == user.id,
            SchoolModerator.school_id == school_id,
            SchoolModerator.is_active == True,  # noqa: E712
        )
    )
    return result.scalar_one_or_none() is not None


async def ensure_can_manage_school(db: AsyncSession, user: User, school_id: int) -> None:
    if not await can_manage_school(db, user, school_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No management scope for this school")


async def board_school_id(db: AsyncSession, board_id: int) -> int:
    result = await db.execute(select(Board.school_id).where(Board.id == board_id))
    school_id = result.scalar_one_or_none()
    if school_id is None:
        raise HTTPException(status_code=404, detail="Board not found")
    return school_id


async def ensure_can_manage_board(db: AsyncSession, user: User, board_id: int) -> int:
    school_id = await board_school_id(db, board_id)
    await ensure_can_manage_school(db, user, school_id)
    return school_id
