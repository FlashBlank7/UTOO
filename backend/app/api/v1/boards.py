from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.school import Board, School
from app.models.user import User
from app.schemas.school import BoardCreateRequest, BoardOut, SchoolBrief
from app.core.schools import BOARD_STATUS_APPROVED, BOARD_STATUS_PENDING, slugify

router = APIRouter()


def _board_out(board: Board, school: School) -> BoardOut:
    return BoardOut(
        id=board.id,
        school_id=board.school_id,
        parent_id=board.parent_id,
        slug=board.slug,
        name=board.name,
        description=board.description,
        status=board.status,
        sort_order=board.sort_order,
        created_by=board.created_by,
        created_at=board.created_at,
        updated_at=board.updated_at,
        school=SchoolBrief(
            id=school.id,
            slug=school.slug,
            name_zh=school.name_zh,
            name_en=school.name_en,
            name_ja=school.name_ja,
            kind=school.kind,
            theme=school.theme,
        ),
    )


@router.post("", response_model=BoardOut, status_code=status.HTTP_201_CREATED)
async def request_board(
    body: BoardCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Board name is required")

    if body.school_id is not None:
        school_result = await db.execute(select(School).where(School.id == body.school_id, School.is_active == True))  # noqa: E712
    elif body.school_slug:
        school_result = await db.execute(select(School).where(School.slug == body.school_slug, School.is_active == True))  # noqa: E712
    else:
        raise HTTPException(status_code=400, detail="School is required")
    school = school_result.scalar_one_or_none()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    parent_id = body.parent_id
    if parent_id is not None:
        parent_result = await db.execute(
            select(Board).where(
                Board.id == parent_id,
                Board.school_id == school.id,
                Board.parent_id.is_(None),
                Board.status == BOARD_STATUS_APPROVED,
            )
        )
        if not parent_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Parent board not found")

    slug = slugify(name, "board")
    exists = await db.execute(select(Board).where(Board.school_id == school.id, Board.slug == slug))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Board already exists")

    board = Board(
        school_id=school.id,
        parent_id=parent_id,
        slug=slug,
        name=name,
        description=body.description.strip() if body.description else None,
        status=BOARD_STATUS_PENDING,
        sort_order=1000,
        created_by=current_user.id,
    )
    db.add(board)
    await db.commit()
    await db.refresh(board)
    return _board_out(board, school)
