from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.moderation import REPORT_RESOLVED, VISIBILITY_DELETED, VISIBILITY_HIDDEN, add_moderation_log, set_comment_visibility, set_post_visibility
from app.core.permissions import ensure_can_manage_board, ensure_can_manage_school, moderated_school_ids
from app.core.schools import BOARD_STATUS_APPROVED, BOARD_STATUS_HIDDEN, BOARD_STATUS_PENDING, BOARD_STATUS_REJECTED, slugify
from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.comment import Comment
from app.models.post import Post
from app.models.report import Report
from app.models.school import Board, School
from app.models.user import User
from app.schemas.report import PatchReportRequest, ReportOut, VisibilityRequest
from app.schemas.school import BoardCreateRequest, BoardOut, BoardPatchRequest, SchoolBrief, SchoolOut, SchoolPatchRequest
from app.schemas.management import ManagementScopeOut, ManagementScopesOut

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


def _school_out(school: School) -> SchoolOut:
    return SchoolOut(
        id=school.id,
        slug=school.slug,
        name_zh=school.name_zh,
        name_en=school.name_en,
        name_ja=school.name_ja,
        country=school.country,
        kind=school.kind,
        rank_source=school.rank_source,
        rank_label=school.rank_label,
        rank_order=school.rank_order,
        theme=school.theme,
        description=school.description,
        is_active=school.is_active,
    )


def _board_out(board: Board, school: School | None = None, children: list[BoardOut] | None = None, parent_name: str | None = None) -> BoardOut:
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
        parent_name=parent_name,
        children=children or [],
    )


async def _managed_schools(db: AsyncSession, user: User) -> list[School]:
    ids = await moderated_school_ids(db, user)
    if not ids:
        return []
    result = await db.execute(select(School).where(School.id.in_(ids), School.is_active == True).order_by(School.kind.desc(), School.rank_order.asc().nullsfirst(), School.name_en.asc()))  # noqa: E712
    return result.scalars().all()


async def _board_tree(db: AsyncSession, school: School, include_hidden: bool = True) -> list[BoardOut]:
    stmt = select(Board).where(Board.school_id == school.id)
    if not include_hidden:
        stmt = stmt.where(Board.status == BOARD_STATUS_APPROVED)
    result = await db.execute(stmt.order_by(Board.parent_id.asc().nullsfirst(), Board.sort_order.asc(), Board.name.asc()))
    boards = result.scalars().all()
    children_by_parent: dict[int, list[BoardOut]] = {}
    roots: list[Board] = []
    for board in boards:
        if board.parent_id:
            children_by_parent.setdefault(board.parent_id, []).append(_board_out(board, school))
        else:
            roots.append(board)
    return [_board_out(board, school, children_by_parent.get(board.id, [])) for board in roots]


@router.get("/scopes", response_model=ManagementScopesOut)
async def get_management_scopes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    schools = await _managed_schools(db, current_user)
    return ManagementScopesOut(
        is_admin=current_user.is_admin,
        scopes=[ManagementScopeOut(school=_school_brief(school), boards=await _board_tree(db, school)) for school in schools],
    )


@router.patch("/schools/{school_id}", response_model=SchoolOut)
async def patch_managed_school(
    school_id: int,
    body: SchoolPatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await ensure_can_manage_school(db, current_user, school_id)
    result = await db.execute(select(School).where(School.id == school_id))
    school = result.scalar_one_or_none()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    if "description" in body.model_fields_set:
        school.description = body.description.strip() if body.description else None
        add_moderation_log(db, current_user, "school", school.id, "moderator_update_description", None)
    await db.commit()
    await db.refresh(school)
    return _school_out(school)


@router.get("/boards", response_model=list[BoardOut])
async def list_managed_boards(
    school_id: int,
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await ensure_can_manage_school(db, current_user, school_id)
    school_result = await db.execute(select(School).where(School.id == school_id))
    school = school_result.scalar_one_or_none()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    stmt = select(Board).where(Board.school_id == school_id)
    if status_filter:
        stmt = stmt.where(Board.status == status_filter)
    result = await db.execute(stmt.order_by(Board.parent_id.asc().nullsfirst(), Board.sort_order.asc(), Board.name.asc()))
    boards = result.scalars().all()
    parent_ids = {board.parent_id for board in boards if board.parent_id is not None}
    parents = {}
    if parent_ids:
        parent_result = await db.execute(select(Board).where(Board.id.in_(parent_ids)))
        parents = {board.id: board for board in parent_result.scalars().all()}
    return [_board_out(board, school, parent_name=parents.get(board.parent_id).name if board.parent_id in parents else None) for board in boards]


@router.post("/boards", response_model=BoardOut, status_code=status.HTTP_201_CREATED)
async def create_managed_board(
    body: BoardCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.school_id is None:
        raise HTTPException(status_code=400, detail="School is required")
    await ensure_can_manage_school(db, current_user, body.school_id)
    school_result = await db.execute(select(School).where(School.id == body.school_id, School.is_active == True))  # noqa: E712
    school = school_result.scalar_one_or_none()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Board name is required")
    parent_id = body.parent_id
    if parent_id is not None:
        parent_result = await db.execute(select(Board).where(Board.id == parent_id, Board.school_id == school.id, Board.parent_id.is_(None)))
        if not parent_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Parent board not found")
    base_slug = slugify(name, "board")
    slug = base_slug
    index = 2
    while True:
        exists = await db.execute(select(Board.id).where(Board.school_id == school.id, Board.slug == slug))
        if not exists.scalar_one_or_none():
            break
        slug = f"{base_slug[:94]}-{index}"
        index += 1
    board = Board(
        school_id=school.id,
        parent_id=parent_id,
        slug=slug,
        name=name,
        description=body.description.strip() if body.description else None,
        status=BOARD_STATUS_APPROVED,
        sort_order=1000,
        created_by=current_user.id,
    )
    db.add(board)
    await db.flush()
    add_moderation_log(db, current_user, "board", board.id, "moderator_create", None)
    await db.commit()
    await db.refresh(board)
    return _board_out(board, school)


@router.patch("/boards/{board_id}", response_model=BoardOut)
async def patch_managed_board(
    board_id: int,
    body: BoardPatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await ensure_can_manage_board(db, current_user, board_id)
    result = await db.execute(select(Board).where(Board.id == board_id))
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Board name is required")
        board.name = name
    if "description" in body.model_fields_set:
        board.description = body.description.strip() if body.description else None
    if body.status is not None:
        if body.status not in {BOARD_STATUS_APPROVED, BOARD_STATUS_PENDING, BOARD_STATUS_REJECTED, BOARD_STATUS_HIDDEN}:
            raise HTTPException(status_code=400, detail="Invalid board status")
        board.status = body.status
    if body.sort_order is not None:
        board.sort_order = body.sort_order
    add_moderation_log(db, current_user, "board", board.id, f"moderator_set_{board.status}", None)
    await db.commit()
    await db.refresh(board)
    school_result = await db.execute(select(School).where(School.id == board.school_id))
    return _board_out(board, school_result.scalar_one_or_none())


@router.patch("/posts/{post_id}/visibility", status_code=status.HTTP_204_NO_CONTENT)
async def set_managed_post_visibility(
    post_id: int,
    body: VisibilityRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.school_id is None:
        raise HTTPException(status_code=400, detail="Post has no school")
    await ensure_can_manage_school(db, current_user, post.school_id)
    if body.visibility not in {VISIBILITY_HIDDEN, VISIBILITY_DELETED, "normal"}:
        raise HTTPException(status_code=400, detail="Invalid visibility")
    set_post_visibility(post, body.visibility)
    add_moderation_log(db, current_user, "post", post.id, f"moderator_set_{body.visibility}", body.reason)
    await db.commit()


@router.patch("/comments/{comment_id}/visibility", status_code=status.HTTP_204_NO_CONTENT)
async def set_managed_comment_visibility(
    comment_id: int,
    body: VisibilityRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    post_result = await db.execute(select(Post).where(Post.id == comment.post_id))
    post = post_result.scalar_one_or_none()
    if not post or post.school_id is None:
        raise HTTPException(status_code=400, detail="Comment has no school")
    await ensure_can_manage_school(db, current_user, post.school_id)
    if body.visibility not in {VISIBILITY_HIDDEN, VISIBILITY_DELETED, "normal"}:
        raise HTTPException(status_code=400, detail="Invalid visibility")
    set_comment_visibility(comment, body.visibility)
    add_moderation_log(db, current_user, "comment", comment.id, f"moderator_set_{body.visibility}", body.reason)
    await db.commit()


async def _report_school_id(db: AsyncSession, report: Report) -> int | None:
    if report.target_type == "post":
        result = await db.execute(select(Post.school_id).where(Post.id == report.target_id))
        return result.scalar_one_or_none()
    if report.target_type == "comment":
        result = await db.execute(select(Comment.post_id).where(Comment.id == report.target_id))
        post_id = result.scalar_one_or_none()
        if post_id is None:
            return None
        post_result = await db.execute(select(Post.school_id).where(Post.id == post_id))
        return post_result.scalar_one_or_none()
    return None


@router.get("/reports", response_model=list[ReportOut])
async def list_managed_reports(
    status_filter: str | None = Query("pending", alias="status"),
    school_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    managed_ids = await moderated_school_ids(db, current_user)
    if school_id is not None:
        await ensure_can_manage_school(db, current_user, school_id)
        managed_ids = {school_id}
    if not managed_ids:
        return []
    stmt = select(Report).order_by(Report.created_at.desc()).limit(200)
    if status_filter:
        stmt = stmt.where(Report.status == status_filter)
    result = await db.execute(stmt)
    reports = result.scalars().all()
    visible: list[Report] = []
    for report in reports:
        target_school_id = await _report_school_id(db, report)
        if target_school_id in managed_ids:
            visible.append(report)
    return visible


@router.patch("/reports/{report_id}", response_model=ReportOut)
async def patch_managed_report(
    report_id: int,
    body: PatchReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    target_school_id = await _report_school_id(db, report)
    if target_school_id is None:
        raise HTTPException(status_code=400, detail="Report target has no school")
    await ensure_can_manage_school(db, current_user, target_school_id)
    if body.action in {"hide", "delete"}:
        visibility = VISIBILITY_HIDDEN if body.action == "hide" else VISIBILITY_DELETED
        if report.target_type == "post":
            target_result = await db.execute(select(Post).where(Post.id == report.target_id))
            target = target_result.scalar_one_or_none()
            if target:
                set_post_visibility(target, visibility)
        elif report.target_type == "comment":
            target_result = await db.execute(select(Comment).where(Comment.id == report.target_id))
            target = target_result.scalar_one_or_none()
            if target:
                set_comment_visibility(target, visibility)
        add_moderation_log(db, current_user, report.target_type, report.target_id, f"moderator_{body.action}", body.resolution)
    elif body.action != "resolve":
        raise HTTPException(status_code=400, detail="Invalid report action")
    report.status = REPORT_RESOLVED
    report.resolved_by = current_user.id
    report.resolution = body.resolution or body.action
    add_moderation_log(db, current_user, "report", report.id, f"moderator_resolve_{body.action}", body.resolution)
    await db.commit()
    await db.refresh(report)
    return report
