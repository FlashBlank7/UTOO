import secrets
import string
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.models.activation_code import ActivationCode, ActivationCodeUsage
from app.models.post import Post
from app.models.agent import Agent
from app.models.comment import Comment
from app.models.report import ModerationLog, Report
from app.models.school import Board, School, SchoolRequest
from app.schemas.admin import (
    AgentOut,
    AgentWithKeyOut,
    CodeOut,
    CodeUsageOut,
    CreateAnnouncementRequest,
    CreateAgentRequest,
    GenerateCodeRequest,
    PatchAgentRequest,
    PatchCodeRequest,
    ResetPasswordRequest,
)
from app.schemas.user import UserOut
from app.schemas.post import PostOut, AuthorInfo
from app.schemas.school import BoardOut, BoardPatchRequest, SchoolBrief, SchoolOut, SchoolPatchRequest, SchoolRequestCreate, SchoolRequestOut, SchoolRequestPatch
from app.schemas.report import (
    ModerationLogOut,
    PatchReportRequest,
    ReportOut,
    UserModerationRequest,
    VisibilityRequest,
)
from app.core.security import hash_password
from app.core.agent_keys import agent_key_prefix, generate_agent_api_key
from app.core.moderation import (
    REPORT_PENDING,
    REPORT_RESOLVED,
    VISIBILITY_DELETED,
    VISIBILITY_HIDDEN,
    VISIBILITY_NORMAL,
    add_moderation_log,
    set_comment_visibility,
    set_post_visibility,
)
from app.core.schools import (
    BOARD_STATUS_APPROVED,
    BOARD_STATUS_HIDDEN,
    BOARD_STATUS_PENDING,
    BOARD_STATUS_REJECTED,
    DEFAULT_SCHOOL_SLUG,
    SCHOOL_REQUEST_APPROVED,
    SCHOOL_REQUEST_PENDING,
    SCHOOL_REQUEST_REJECTED,
    add_school_alias,
    create_default_boards,
    parse_aliases,
    unique_school_slug,
)
from app.dependencies import get_current_admin

router = APIRouter()


def _random_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _agent_response_with_key(agent: Agent, api_key: str) -> AgentWithKeyOut:
    return AgentWithKeyOut(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        api_key_prefix=agent.api_key_prefix,
        api_key=api_key,
        is_active=agent.is_active,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        last_posted_at=agent.last_posted_at,
    )


def _validate_visibility(visibility: str) -> str:
    if visibility not in {VISIBILITY_NORMAL, VISIBILITY_HIDDEN, VISIBILITY_DELETED}:
        raise HTTPException(status_code=400, detail="Invalid visibility")
    return visibility


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


def _board_out(board: Board, school: School | None = None, parent_name: str | None = None) -> BoardOut:
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
    )


def _school_request_out(request: SchoolRequest, created_school: School | None = None) -> SchoolRequestOut:
    return SchoolRequestOut(
        id=request.id,
        requested_by=request.requested_by,
        name_zh=request.name_zh,
        name_en=request.name_en,
        name_ja=request.name_ja,
        aliases=request.aliases,
        website=request.website,
        description=request.description,
        status=request.status,
        created_school=_school_brief(created_school),
        created_school_id=request.created_school_id,
        reviewed_by=request.reviewed_by,
        reviewed_at=request.reviewed_at,
        created_at=request.created_at,
        updated_at=request.updated_at,
    )


async def _create_real_school_from_input(db: AsyncSession, body: SchoolRequestCreate) -> School:
    name_zh = body.name_zh.strip()
    if not name_zh:
        raise HTTPException(status_code=400, detail="School name is required")
    primary_name = body.name_en.strip() if body.name_en else name_zh
    slug = await unique_school_slug(db, primary_name)
    school = School(
        slug=slug,
        name_zh=name_zh,
        name_en=body.name_en.strip() if body.name_en else name_zh,
        name_ja=body.name_ja.strip() if body.name_ja else name_zh,
        country="Japan",
        kind="real",
        rank_source=None,
        rank_label=None,
        rank_order=None,
        theme="standard",
        description=body.description.strip() if body.description else None,
        is_active=True,
    )
    db.add(school)
    await db.flush()
    for alias, locale in [
        (school.name_zh, "zh"),
        (school.name_en, "en"),
        (school.name_ja, "ja"),
    ]:
        await add_school_alias(db, school, alias, locale)
    for alias in parse_aliases(body.aliases):
        await add_school_alias(db, school, alias)
    await create_default_boards(db, school)
    return school


def _user_out(user: User, school: School | None = None) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        department=user.department,
        school=_school_brief(school),
        school_name_custom=user.school_name_custom,
        email=user.email,
        is_admin=user.is_admin,
        is_banned=user.is_banned,
        muted_until=user.muted_until,
        created_at=user.created_at,
    )


async def _user_with_school(db: AsyncSession, user: User) -> UserOut:
    school = None
    if user.school_id:
        school_result = await db.execute(select(School).where(School.id == user.school_id))
        school = school_result.scalar_one_or_none()
    return _user_out(user, school)


async def _notice_board_for_announcement(
    db: AsyncSession,
    school_id: int | None,
    board_id: int | None,
) -> tuple[School, Board]:
    if board_id is not None:
        board_result = await db.execute(select(Board).where(Board.id == board_id, Board.status == BOARD_STATUS_APPROVED))
        board = board_result.scalar_one_or_none()
        if not board or board.slug != "notice":
            raise HTTPException(status_code=400, detail="Announcement board must be an approved notice board")
        school_result = await db.execute(select(School).where(School.id == board.school_id, School.is_active == True))  # noqa: E712
        school = school_result.scalar_one_or_none()
        if not school:
            raise HTTPException(status_code=400, detail="Invalid school")
        return school, board

    stmt = select(School).where(School.is_active == True)  # noqa: E712
    if school_id is not None:
        stmt = stmt.where(School.id == school_id)
    else:
        stmt = stmt.where(School.slug == DEFAULT_SCHOOL_SLUG)
    school_result = await db.execute(stmt)
    school = school_result.scalar_one_or_none()
    if not school:
        raise HTTPException(status_code=400, detail="Invalid school")
    board_result = await db.execute(
        select(Board).where(
            Board.school_id == school.id,
            Board.parent_id.is_(None),
            Board.slug == "notice",
            Board.status == BOARD_STATUS_APPROVED,
        )
    )
    board = board_result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=400, detail="Notice board is missing")
    return school, board


async def _target_author(db: AsyncSession, target_type: str, target_id: int) -> User | None:
    if target_type == "post":
        result = await db.execute(select(Post).where(Post.id == target_id))
        post = result.scalar_one_or_none()
        if post and post.author_id:
            user_result = await db.execute(select(User).where(User.id == post.author_id))
            return user_result.scalar_one_or_none()
    if target_type == "comment":
        result = await db.execute(select(Comment).where(Comment.id == target_id))
        comment = result.scalar_one_or_none()
        if comment:
            user_result = await db.execute(select(User).where(User.id == comment.author_id))
            return user_result.scalar_one_or_none()
    return None


@router.get("/codes", response_model=list[CodeOut])
async def list_codes(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(ActivationCode).order_by(ActivationCode.created_at.desc()))
    return result.scalars().all()


@router.post("/codes", response_model=CodeOut, status_code=status.HTTP_201_CREATED)
async def generate_code(
    body: GenerateCodeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    code = ActivationCode(code=_random_code(), created_by=current_user.id, max_uses=body.max_uses)
    db.add(code)
    await db.commit()
    await db.refresh(code)
    return code


@router.get("/codes/{code_id}/usages", response_model=list[CodeUsageOut])
async def code_usages(
    code_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(ActivationCodeUsage).where(ActivationCodeUsage.code_id == code_id)
    )
    usages = result.scalars().all()
    if not usages:
        return []

    user_ids = [u.user_id for u in usages]
    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users = {u.id: u for u in users_result.scalars().all()}

    return [
        CodeUsageOut(
            user_id=u.user_id,
            username=users[u.user_id].username,
            display_name=users[u.user_id].display_name,
            department=users[u.user_id].department,
            school_name=users[u.user_id].school_name_custom,
            used_at=u.used_at,
        )
        for u in usages
    ]


@router.patch("/codes/{code_id}", response_model=CodeOut)
async def patch_code(
    code_id: int,
    body: PatchCodeRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(ActivationCode).where(ActivationCode.id == code_id))
    code = result.scalar_one_or_none()
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")
    if body.is_active is not None:
        code.is_active = body.is_active
    if body.max_uses is not None:
        code.max_uses = body.max_uses
    await db.commit()
    await db.refresh(code)
    return code


@router.get("/users", response_model=list[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    school_ids = list({u.school_id for u in users if u.school_id is not None})
    schools = {}
    if school_ids:
        school_result = await db.execute(select(School).where(School.id.in_(school_ids)))
        schools = {s.id: s for s in school_result.scalars().all()}
    return [_user_out(user, schools.get(user.school_id)) for user in users]


@router.patch("/users/{user_id}/moderation", response_model=UserOut)
async def moderate_user(
    user_id: int,
    body: UserModerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.is_banned is not None:
        user.is_banned = body.is_banned
        add_moderation_log(
            db,
            current_user,
            "user",
            user.id,
            "ban" if body.is_banned else "unban",
            body.reason,
        )
    if body.clear_mute:
        user.muted_until = None
        add_moderation_log(db, current_user, "user", user.id, "unmute", body.reason)
    elif body.mute_days is not None:
        if body.mute_days <= 0:
            raise HTTPException(status_code=400, detail="mute_days must be positive")
        user.muted_until = datetime.now(timezone.utc) + timedelta(days=body.mute_days)
        add_moderation_log(db, current_user, "user", user.id, "mute", body.reason)

    await db.commit()
    await db.refresh(user)
    return await _user_with_school(db, user)


@router.get("/board-requests", response_model=list[BoardOut])
async def list_board_requests(
    status_filter: str | None = Query(BOARD_STATUS_PENDING, alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    stmt = select(Board).order_by(Board.created_at.desc())
    if status_filter:
        stmt = stmt.where(Board.status == status_filter)
    result = await db.execute(stmt)
    boards = result.scalars().all()
    if not boards:
        return []
    school_ids = list({board.school_id for board in boards})
    school_result = await db.execute(select(School).where(School.id.in_(school_ids)))
    schools = {school.id: school for school in school_result.scalars().all()}
    parent_ids = list({board.parent_id for board in boards if board.parent_id is not None})
    parents = {}
    if parent_ids:
        parent_result = await db.execute(select(Board).where(Board.id.in_(parent_ids)))
        parents = {board.id: board for board in parent_result.scalars().all()}
    return [_board_out(board, schools.get(board.school_id), parents.get(board.parent_id).name if board.parent_id in parents else None) for board in boards]


@router.patch("/boards/{board_id}", response_model=BoardOut)
async def patch_board(
    board_id: int,
    body: BoardPatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
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
        if (
            board.parent_id is None
            and board.status == BOARD_STATUS_APPROVED
            and body.status != BOARD_STATUS_APPROVED
        ):
            raise HTTPException(status_code=400, detail="Approved top-level boards cannot be removed")
        board.status = body.status
        add_moderation_log(db, current_user, "board", board.id, f"set_{body.status}", None)
    if body.sort_order is not None:
        board.sort_order = body.sort_order

    await db.commit()
    await db.refresh(board)
    school_result = await db.execute(select(School).where(School.id == board.school_id))
    parent_name = None
    if board.parent_id:
        parent_result = await db.execute(select(Board).where(Board.id == board.parent_id))
        parent = parent_result.scalar_one_or_none()
        parent_name = parent.name if parent else None
    return _board_out(board, school_result.scalar_one_or_none(), parent_name)


@router.post("/schools", response_model=SchoolOut, status_code=status.HTTP_201_CREATED)
async def create_school(
    body: SchoolRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    school = await _create_real_school_from_input(db, body)
    add_moderation_log(db, current_user, "school", school.id, "create", school.slug)
    await db.commit()
    await db.refresh(school)
    return _school_out(school)


@router.patch("/schools/{school_id}", response_model=SchoolOut)
async def patch_school(
    school_id: int,
    body: SchoolPatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    result = await db.execute(select(School).where(School.id == school_id))
    school = result.scalar_one_or_none()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    if "description" in body.model_fields_set:
        school.description = body.description.strip() if body.description else None
        add_moderation_log(db, current_user, "school", school.id, "update_description", None)

    await db.commit()
    await db.refresh(school)
    return _school_out(school)


@router.get("/school-requests", response_model=list[SchoolRequestOut])
async def list_school_requests(
    status_filter: str | None = Query(SCHOOL_REQUEST_PENDING, alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    stmt = select(SchoolRequest).order_by(SchoolRequest.created_at.desc())
    if status_filter:
        stmt = stmt.where(SchoolRequest.status == status_filter)
    result = await db.execute(stmt)
    requests = result.scalars().all()
    if not requests:
        return []
    school_ids = list({request.created_school_id for request in requests if request.created_school_id is not None})
    schools = {}
    if school_ids:
        school_result = await db.execute(select(School).where(School.id.in_(school_ids)))
        schools = {school.id: school for school in school_result.scalars().all()}
    return [_school_request_out(request, schools.get(request.created_school_id)) for request in requests]


@router.patch("/school-requests/{request_id}", response_model=SchoolRequestOut)
async def patch_school_request(
    request_id: int,
    body: SchoolRequestPatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    if body.status not in {SCHOOL_REQUEST_APPROVED, SCHOOL_REQUEST_REJECTED}:
        raise HTTPException(status_code=400, detail="Invalid school request status")
    result = await db.execute(select(SchoolRequest).where(SchoolRequest.id == request_id))
    request = result.scalar_one_or_none()
    if not request:
        raise HTTPException(status_code=404, detail="School request not found")
    if request.status != SCHOOL_REQUEST_PENDING:
        raise HTTPException(status_code=400, detail="School request already reviewed")

    created_school = None
    request.status = body.status
    request.reviewed_by = current_user.id
    request.reviewed_at = datetime.now(timezone.utc)

    if body.status == SCHOOL_REQUEST_APPROVED:
        school = await _create_real_school_from_input(
            db,
            SchoolRequestCreate(
                name_zh=request.name_zh,
                name_en=request.name_en,
                name_ja=request.name_ja,
                aliases=request.aliases,
                website=request.website,
                description=request.description,
            ),
        )
        request.created_school_id = school.id
        created_school = school
        add_moderation_log(db, current_user, "school_request", request.id, "approve", school.slug)
    else:
        add_moderation_log(db, current_user, "school_request", request.id, "reject", None)

    await db.commit()
    await db.refresh(request)
    if request.created_school_id and not created_school:
        school_result = await db.execute(select(School).where(School.id == request.created_school_id))
        created_school = school_result.scalar_one_or_none()
    return _school_request_out(request, created_school)


@router.get("/agents", response_model=list[AgentOut])
async def list_agents(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Agent).order_by(Agent.created_at.desc()))
    return result.scalars().all()


@router.post("/agents", response_model=AgentWithKeyOut, status_code=status.HTTP_201_CREATED)
async def create_agent(
    body: CreateAgentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Agent name is required")

    exists = await db.execute(select(Agent).where(Agent.name == name))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Agent name already exists")

    api_key = generate_agent_api_key()
    agent = Agent(
        name=name,
        description=body.description.strip() if body.description else None,
        api_key_prefix=agent_key_prefix(api_key),
        api_key_hash=hash_password(api_key),
        created_by=current_user.id,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return _agent_response_with_key(agent, api_key)


@router.patch("/agents/{agent_id}", response_model=AgentOut)
async def patch_agent(
    agent_id: int,
    body: PatchAgentRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Agent name is required")
        exists = await db.execute(select(Agent).where(Agent.name == name, Agent.id != agent.id))
        if exists.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Agent name already exists")
        agent.name = name
    if "description" in body.model_fields_set:
        agent.description = body.description.strip() if body.description else None
    if body.is_active is not None:
        agent.is_active = body.is_active

    await db.commit()
    await db.refresh(agent)
    return agent


@router.post("/agents/{agent_id}/reset-key", response_model=AgentWithKeyOut)
async def reset_agent_key(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    api_key = generate_agent_api_key()
    agent.api_key_prefix = agent_key_prefix(api_key)
    agent.api_key_hash = hash_password(api_key)
    await db.commit()
    await db.refresh(agent)
    return _agent_response_with_key(agent, api_key)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    set_post_visibility(post, VISIBILITY_DELETED)
    add_moderation_log(db, _, "post", post.id, "delete", "admin delete")
    await db.commit()


@router.patch("/posts/{post_id}/visibility", status_code=status.HTTP_204_NO_CONTENT)
async def set_admin_post_visibility(
    post_id: int,
    body: VisibilityRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    visibility = _validate_visibility(body.visibility)
    set_post_visibility(post, visibility)
    add_moderation_log(db, current_user, "post", post.id, f"set_{visibility}", body.reason)
    await db.commit()


@router.patch("/comments/{comment_id}/visibility", status_code=status.HTTP_204_NO_CONTENT)
async def set_admin_comment_visibility(
    comment_id: int,
    body: VisibilityRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    visibility = _validate_visibility(body.visibility)
    set_comment_visibility(comment, visibility)
    add_moderation_log(db, current_user, "comment", comment.id, f"set_{visibility}", body.reason)
    await db.commit()


@router.get("/reports", response_model=list[ReportOut])
async def list_reports(
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    stmt = select(Report).order_by(Report.created_at.desc())
    if status_filter:
        stmt = stmt.where(Report.status == status_filter)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.patch("/reports/{report_id}", response_model=ReportOut)
async def patch_report(
    report_id: int,
    body: PatchReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    action = body.action
    if action in {"hide", "delete"}:
        visibility = VISIBILITY_HIDDEN if action == "hide" else VISIBILITY_DELETED
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
        add_moderation_log(db, current_user, report.target_type, report.target_id, action, body.resolution)
    elif action == "mute":
        author = await _target_author(db, report.target_type, report.target_id)
        if not author:
            raise HTTPException(status_code=400, detail="Target has no user author to mute")
        days = body.mute_days or 1
        if days <= 0:
            raise HTTPException(status_code=400, detail="mute_days must be positive")
        author.muted_until = datetime.now(timezone.utc) + timedelta(days=days)
        add_moderation_log(db, current_user, "user", author.id, "mute", body.resolution)
    elif action != "resolve":
        raise HTTPException(status_code=400, detail="Invalid report action")

    report.status = REPORT_RESOLVED
    report.resolved_by = current_user.id
    report.resolution = body.resolution or action
    add_moderation_log(db, current_user, "report", report.id, f"resolve_{action}", body.resolution)
    await db.commit()
    await db.refresh(report)
    return report


@router.get("/moderation-logs", response_model=list[ModerationLogOut])
async def list_moderation_logs(
    target_type: str | None = Query(None),
    action: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    stmt = select(ModerationLog).order_by(ModerationLog.created_at.desc()).limit(200)
    if target_type:
        stmt = stmt.where(ModerationLog.target_type == target_type)
    if action:
        stmt = stmt.where(ModerationLog.action == action)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/announcements", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    body: CreateAnnouncementRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    title = body.title.strip()
    content = body.content.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    school, board = await _notice_board_for_announcement(db, body.school_id, body.board_id)
    post = Post(
        author_id=current_user.id,
        title=title,
        content=content,
        category="公告",
        school_id=school.id,
        board_id=board.id,
        is_pinned=True,
        visibility=VISIBILITY_NORMAL,
    )
    db.add(post)
    await db.flush()
    add_moderation_log(db, current_user, "post", post.id, "create_announcement", None)
    await db.commit()
    await db.refresh(post)
    return PostOut(
        id=post.id,
        title=post.title,
        content=post.content,
        is_anonymous=False,
        department_tag=None,
        category=post.category,
        school=_school_brief(school),
        board=_board_out(board, school),
        visibility=post.visibility,
        is_pinned=post.is_pinned,
        created_at=post.created_at,
        updated_at=post.updated_at,
        author=AuthorInfo(
            display_name=current_user.display_name or f"用户{current_user.id}",
            department=current_user.department,
            school=_school_brief(school),
            school_name_custom=current_user.school_name_custom,
            source="user",
            id=current_user.id,
        ),
        comment_count=0,
        can_edit=True,
        can_delete=True,
    )


@router.patch("/users/{user_id}/password", response_model=UserOut)
async def reset_user_password(
    user_id: int,
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(body.new_password)
    await db.commit()
    await db.refresh(user)
    return await _user_with_school(db, user)
