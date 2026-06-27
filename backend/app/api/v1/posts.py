from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.db.session import get_db
from app.models.post import Post
from app.models.user import User
from app.models.comment import Comment
from app.models.agent import Agent
from app.models.school import Board, School
from app.schemas.post import PostCreate, PostOut, PostUpdate, AuthorInfo
from app.schemas.school import BoardOut, SchoolBrief
from app.dependencies import get_current_user
from app.core.schools import BOARD_STATUS_APPROVED, DEFAULT_SCHOOL_SLUG, default_board_for_category
from app.core.moderation import (
    VISIBILITY_DELETED,
    VISIBILITY_HIDDEN,
    VISIBILITY_NORMAL,
    contains_sensitive_word,
    create_sensitive_report,
    enforce_rate_limit,
    ensure_can_publish,
    set_post_visibility,
)
from app.core.yutoko import maybe_create_yutoko_comment

router = APIRouter()

ANON_DISPLAY = "匿名用户"
USER_CATEGORIES = {"课程", "研究室", "生活", "租房", "就职", "闲聊"}
ADMIN_CATEGORIES = USER_CATEGORIES | {"公告"}


def _normalize_category(category: str | None, is_admin: bool = False) -> str:
    normalized = (category or "闲聊").strip()
    allowed = ADMIN_CATEGORIES if is_admin else USER_CATEGORIES
    if normalized not in allowed:
        raise HTTPException(status_code=400, detail="Invalid category")
    return normalized


def _author_info(user: User, is_anonymous: bool) -> AuthorInfo:
    if is_anonymous:
        return AuthorInfo(display_name=ANON_DISPLAY, source="user")
    school = getattr(user, "_utoo_school", None)
    return AuthorInfo(
        display_name=user.display_name or f"用户{user.id}",
        department=user.department,
        school=_school_brief(school),
        school_name_custom=user.school_name_custom,
        source="user",
        id=user.id,
    )


def _agent_author_info(agent: Agent) -> AuthorInfo:
    return AuthorInfo(display_name=agent.name, source="agent", id=agent.id)


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
    )


def _board_out(board: Board | None, school: School | None = None) -> BoardOut | None:
    if not board:
        return None
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
    )


def _can_manage(post: Post, user: User | None) -> bool:
    return bool(user and (user.is_admin or post.author_id == user.id))


def _post_to_out(
    post: Post,
    author: User | None,
    comment_count: int,
    viewer: User | None = None,
    agent: Agent | None = None,
    school: School | None = None,
    board: Board | None = None,
    parent_board: Board | None = None,
) -> PostOut:
    can_manage = _can_manage(post, viewer)
    if agent:
        author_info = _agent_author_info(agent)
    elif author:
        author_info = _author_info(author, post.is_anonymous)
    else:
        author_info = AuthorInfo(display_name="未知作者", source="user")

    return PostOut(
        id=post.id,
        title=post.title,
        content=post.content,
        is_anonymous=post.is_anonymous,
        department_tag=post.department_tag,
        category=post.category,
        school=_school_brief(school),
        board=_board_out(board, school),
        parent_board=_board_out(parent_board, school),
        visibility=post.visibility,
        is_pinned=post.is_pinned,
        created_at=post.created_at,
        updated_at=post.updated_at,
        author=author_info,
        comment_count=comment_count,
        can_edit=can_manage,
        can_delete=can_manage,
    )


async def _resolve_post_board(
    db: AsyncSession,
    board_id: int | None,
    category: str | None,
    user: User,
) -> tuple[School, Board, str]:
    if board_id is not None:
        board_result = await db.execute(select(Board).where(Board.id == board_id, Board.status == BOARD_STATUS_APPROVED))
        board = board_result.scalar_one_or_none()
        if not board:
            raise HTTPException(status_code=400, detail="Invalid board")
        school_result = await db.execute(select(School).where(School.id == board.school_id, School.is_active == True))  # noqa: E712
        school = school_result.scalar_one_or_none()
        if not school:
            raise HTTPException(status_code=400, detail="Invalid school")
        if board.slug == "notice" and not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin only")
        if board.slug == "notice":
            return school, board, "公告"
        if board.name in USER_CATEGORIES:
            return school, board, board.name
        return school, board, _normalize_category(category, user.is_admin)

    school_id = user.school_id
    if not school_id:
        default_result = await db.execute(select(School).where(School.slug == DEFAULT_SCHOOL_SLUG))
        default_school = default_result.scalar_one_or_none()
        school_id = default_school.id if default_school else None
    board = await default_board_for_category(db, school_id, category)
    school_result = await db.execute(select(School).where(School.id == board.school_id))
    school = school_result.scalar_one()
    return school, board, _normalize_category(category, user.is_admin)


@router.get("", response_model=list[PostOut])
async def list_posts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    department: str | None = Query(None),
    category: str | None = Query(None),
    school_id: int | None = Query(None),
    school_slug: str | None = Query(None),
    board_id: int | None = Query(None),
    q: str | None = Query(None),
    include_deleted: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    offset = (page - 1) * page_size
    is_admin_view = bool(current_user and current_user.is_admin)
    stmt = select(Post)
    if include_deleted and not is_admin_view:
        raise HTTPException(status_code=403, detail="Admin only")
    if not include_deleted:
        stmt = stmt.where(Post.visibility != VISIBILITY_DELETED, Post.is_deleted == False)  # noqa: E712
    if not is_admin_view:
        stmt = stmt.where(Post.visibility == VISIBILITY_NORMAL, Post.is_deleted == False)  # noqa: E712
    if not category and not board_id and not is_admin_view:
        stmt = stmt.where(Post.category != "公告")
    if department:
        stmt = stmt.where(Post.department_tag == department)
    if school_id:
        stmt = stmt.where(Post.school_id == school_id)
    if school_slug:
        school_result = await db.execute(select(School).where(School.slug == school_slug))
        school = school_result.scalar_one_or_none()
        if not school:
            return []
        stmt = stmt.where(Post.school_id == school.id)
    if board_id:
        child_result = await db.execute(select(Board.id).where(Board.parent_id == board_id, Board.status == BOARD_STATUS_APPROVED))
        board_ids = [board_id, *[row[0] for row in child_result.all()]]
        stmt = stmt.where(Post.board_id.in_(board_ids))
    if category:
        stmt = stmt.where(Post.category == category)
    if q and q.strip():
        keyword = f"%{q.strip()}%"
        stmt = stmt.where(or_(Post.title.ilike(keyword), Post.content.ilike(keyword)))
    stmt = stmt.order_by(Post.is_pinned.desc(), Post.created_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(stmt)
    posts = result.scalars().all()

    if not posts:
        return []

    author_ids = [p.author_id for p in posts if p.author_id is not None]
    users = {}
    if author_ids:
        users_result = await db.execute(select(User).where(User.id.in_(author_ids)))
        users = {u.id: u for u in users_result.scalars().all()}

    user_school_ids = list({u.school_id for u in users.values() if u.school_id is not None})
    user_schools = {}
    if user_school_ids:
        user_school_result = await db.execute(select(School).where(School.id.in_(user_school_ids)))
        user_schools = {s.id: s for s in user_school_result.scalars().all()}
        for user in users.values():
            user._utoo_school = user_schools.get(user.school_id)

    agent_ids = [p.agent_id for p in posts if p.agent_id is not None]
    agents = {}
    if agent_ids:
        agents_result = await db.execute(select(Agent).where(Agent.id.in_(agent_ids)))
        agents = {a.id: a for a in agents_result.scalars().all()}

    post_ids = [p.id for p in posts]
    counts_result = await db.execute(
        select(Comment.post_id, func.count(Comment.id))
        .where(
            Comment.post_id.in_(post_ids),
            Comment.visibility == VISIBILITY_NORMAL,
            Comment.is_deleted == False,  # noqa: E712
        )
        .group_by(Comment.post_id)
    )
    counts = {row[0]: row[1] for row in counts_result.all()}

    school_ids = list({p.school_id for p in posts if p.school_id is not None})
    schools = {}
    if school_ids:
        school_result = await db.execute(select(School).where(School.id.in_(school_ids)))
        schools = {s.id: s for s in school_result.scalars().all()}
    board_ids_all = list({p.board_id for p in posts if p.board_id is not None})
    boards = {}
    parent_ids: set[int] = set()
    if board_ids_all:
        board_result = await db.execute(select(Board).where(Board.id.in_(board_ids_all)))
        boards = {b.id: b for b in board_result.scalars().all()}
        parent_ids = {b.parent_id for b in boards.values() if b.parent_id is not None}
    parent_boards = {}
    if parent_ids:
        parent_result = await db.execute(select(Board).where(Board.id.in_(parent_ids)))
        parent_boards = {b.id: b for b in parent_result.scalars().all()}

    return [
        _post_to_out(
            p,
            users.get(p.author_id) if p.author_id is not None else None,
            counts.get(p.id, 0),
            current_user,
            agents.get(p.agent_id) if p.agent_id is not None else None,
            schools.get(p.school_id) if p.school_id is not None else None,
            boards.get(p.board_id) if p.board_id is not None else None,
            parent_boards.get(boards[p.board_id].parent_id) if p.board_id in boards and boards[p.board_id].parent_id else None,
        )
        for p in posts
    ]


@router.post("", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(
    body: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    title = body.title.strip()
    content = body.content.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    ensure_can_publish(current_user)
    await enforce_rate_limit(db, "user", current_user.id, "post", 60)

    school, board, normalized_category = await _resolve_post_board(db, body.board_id, body.category, current_user)
    post = Post(
        author_id=current_user.id,
        title=title,
        content=content,
        is_anonymous=body.is_anonymous,
        department_tag=body.department_tag.strip() if body.department_tag else None,
        category=normalized_category,
        school_id=school.id,
        board_id=board.id,
    )
    if contains_sensitive_word(title, content):
        set_post_visibility(post, VISIBILITY_HIDDEN)
    db.add(post)
    await db.flush()
    if post.visibility == VISIBILITY_HIDDEN:
        await create_sensitive_report(db, "post", post.id, "Post matched sensitive words")
    yutoko_comment = await maybe_create_yutoko_comment(db, post)
    await db.commit()
    await db.refresh(post)
    current_user._utoo_school = school
    return _post_to_out(post, current_user, 1 if yutoko_comment else 0, current_user, None, school, board)


@router.get("/{post_id}", response_model=PostOut)
async def get_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    is_admin_view = bool(current_user and current_user.is_admin)
    stmt = select(Post).where(
        Post.id == post_id,
        Post.visibility != VISIBILITY_DELETED,
        Post.is_deleted == False,  # noqa: E712
    )
    if not is_admin_view:
        stmt = stmt.where(Post.visibility == VISIBILITY_NORMAL, Post.is_deleted == False)  # noqa: E712
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    author = None
    agent = None
    school = None
    board = None
    parent_board = None
    if post.author_id is not None:
        author_result = await db.execute(select(User).where(User.id == post.author_id))
        author = author_result.scalar_one()
        if author.school_id:
            user_school_result = await db.execute(select(School).where(School.id == author.school_id))
            author._utoo_school = user_school_result.scalar_one_or_none()
    if post.agent_id is not None:
        agent_result = await db.execute(select(Agent).where(Agent.id == post.agent_id))
        agent = agent_result.scalar_one()
    if post.school_id is not None:
        school_result = await db.execute(select(School).where(School.id == post.school_id))
        school = school_result.scalar_one_or_none()
    if post.board_id is not None:
        board_result = await db.execute(select(Board).where(Board.id == post.board_id))
        board = board_result.scalar_one_or_none()
        if board and board.parent_id:
            parent_result = await db.execute(select(Board).where(Board.id == board.parent_id))
            parent_board = parent_result.scalar_one_or_none()

    count_result = await db.execute(
        select(func.count(Comment.id)).where(
            Comment.post_id == post_id,
            Comment.visibility == VISIBILITY_NORMAL,
            Comment.is_deleted == False,  # noqa: E712
        )
    )
    count = count_result.scalar_one()

    return _post_to_out(post, author, count, current_user, agent, school, board, parent_board)


@router.patch("/{post_id}", response_model=PostOut)
async def update_post(
    post_id: int,
    body: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id, Post.visibility != VISIBILITY_DELETED))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if not _can_manage(post, current_user):
        raise HTTPException(status_code=403, detail="Not allowed")

    if body.title is not None:
        title = body.title.strip()
        if not title:
            raise HTTPException(status_code=400, detail="Title is required")
        post.title = title
    if body.content is not None:
        content = body.content.strip()
        if not content:
            raise HTTPException(status_code=400, detail="Content is required")
        post.content = content
    if contains_sensitive_word(post.title, post.content):
        set_post_visibility(post, VISIBILITY_HIDDEN)
    if "department_tag" in body.model_fields_set:
        post.department_tag = body.department_tag.strip() if body.department_tag else None
    school = None
    board = None
    parent_board = None
    if body.board_id is not None:
        school, board, normalized_category = await _resolve_post_board(db, body.board_id, body.category or post.category, current_user)
        post.school_id = school.id
        post.board_id = board.id
        post.category = normalized_category
    if body.category is not None:
        if body.board_id is None:
            school, board, normalized_category = await _resolve_post_board(db, None, body.category, current_user)
            post.school_id = school.id
            post.board_id = board.id
            post.category = normalized_category
    if body.is_pinned is not None:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin only")
        post.is_pinned = body.is_pinned
        if body.is_pinned:
            post.category = "公告"

    await db.flush()
    if post.visibility == VISIBILITY_HIDDEN:
        await create_sensitive_report(db, "post", post.id, "Edited post matched sensitive words")
    await db.commit()
    await db.refresh(post)

    author = None
    agent = None
    if post.author_id is not None:
        author_result = await db.execute(select(User).where(User.id == post.author_id))
        author = author_result.scalar_one()
        if author.school_id:
            user_school_result = await db.execute(select(School).where(School.id == author.school_id))
            author._utoo_school = user_school_result.scalar_one_or_none()
    if post.agent_id is not None:
        agent_result = await db.execute(select(Agent).where(Agent.id == post.agent_id))
        agent = agent_result.scalar_one()
    if post.school_id is not None:
        school_result = await db.execute(select(School).where(School.id == post.school_id))
        school = school_result.scalar_one_or_none()
    if post.board_id is not None:
        board_result = await db.execute(select(Board).where(Board.id == post.board_id))
        board = board_result.scalar_one_or_none()
        if board and board.parent_id:
            parent_result = await db.execute(select(Board).where(Board.id == board.parent_id))
            parent_board = parent_result.scalar_one_or_none()
    count_result = await db.execute(
        select(func.count(Comment.id)).where(
            Comment.post_id == post_id,
            Comment.visibility == VISIBILITY_NORMAL,
            Comment.is_deleted == False,  # noqa: E712
        )
    )
    return _post_to_out(post, author, count_result.scalar_one(), current_user, agent, school, board, parent_board)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id, Post.visibility != VISIBILITY_DELETED))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")
    set_post_visibility(post, VISIBILITY_DELETED)
    await db.commit()
