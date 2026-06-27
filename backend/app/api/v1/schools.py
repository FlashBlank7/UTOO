from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.school import Board, School, SchoolAlias
from app.schemas.school import BoardOut, SchoolBrief, SchoolMatchOut, SchoolOut
from app.core.schools import BOARD_STATUS_APPROVED, normalize_school_alias

router = APIRouter()


def _school_brief(school: School | None) -> SchoolBrief | None:
    if not school:
        return None
    return SchoolBrief(
        id=school.id,
        slug=school.slug,
        name_zh=school.name_zh,
        name_en=school.name_en,
        name_ja=school.name_ja,
        kind=school.kind,
        theme=school.theme,
        description=school.description,
    )


def _board_out(board: Board, school: School | None = None, children: list[BoardOut] | None = None) -> BoardOut:
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
        school=_school_brief(school),
        children=children or [],
    )


@router.get("", response_model=list[SchoolOut])
async def list_schools(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(School).where(School.is_active == True).order_by(School.kind.desc(), School.rank_order.asc().nullsfirst(), School.name_en.asc())  # noqa: E712
    )
    return result.scalars().all()


@router.get("/match", response_model=list[SchoolMatchOut])
async def match_schools(q: str = Query(""), db: AsyncSession = Depends(get_db)):
    query = q.strip()
    if not query:
        return []
    normalized = normalize_school_alias(query)
    alias_result = await db.execute(
        select(SchoolAlias, School)
        .join(School, School.id == SchoolAlias.school_id)
        .where(
            School.is_active == True,  # noqa: E712
            or_(SchoolAlias.alias_normalized == normalized, SchoolAlias.alias.ilike(f"%{query}%")),
        )
        .limit(10)
    )
    seen: set[int] = set()
    matches: list[SchoolMatchOut] = []
    for _, school in alias_result.all():
        if school.id in seen:
            continue
        seen.add(school.id)
        matches.append(SchoolMatchOut(matched=True, school=_school_brief(school)))
    if matches:
        return matches
    return [SchoolMatchOut(matched=False, custom_name=query)]


@router.get("/{slug}/boards", response_model=list[BoardOut])
async def list_school_boards(slug: str, db: AsyncSession = Depends(get_db)):
    school_result = await db.execute(select(School).where(School.slug == slug, School.is_active == True))  # noqa: E712
    school = school_result.scalar_one_or_none()
    if not school:
        return []
    result = await db.execute(
        select(Board)
        .where(Board.school_id == school.id, Board.status == BOARD_STATUS_APPROVED)
        .order_by(Board.parent_id.asc().nullsfirst(), Board.sort_order.asc(), Board.name.asc())
    )
    boards = result.scalars().all()
    children_by_parent: dict[int, list[BoardOut]] = {}
    roots: list[Board] = []
    for board in boards:
        if board.parent_id:
            children_by_parent.setdefault(board.parent_id, []).append(_board_out(board, school))
        else:
            roots.append(board)
    return [_board_out(board, school, children_by_parent.get(board.id, [])) for board in roots]
