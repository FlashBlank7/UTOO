from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.db.session import get_db
from app.models.post import Post
from app.models.user import User
from app.models.comment import Comment
from app.models.agent import Agent
from app.schemas.post import PostCreate, PostOut, PostUpdate, AuthorInfo
from app.dependencies import get_current_user
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
    return AuthorInfo(
        display_name=user.display_name or f"用户{user.id}",
        department=user.department,
        source="user",
        id=user.id,
    )


def _agent_author_info(agent: Agent) -> AuthorInfo:
    return AuthorInfo(display_name=agent.name, source="agent", id=agent.id)


def _can_manage(post: Post, user: User | None) -> bool:
    return bool(user and (user.is_admin or post.author_id == user.id))


def _post_to_out(
    post: Post,
    author: User | None,
    comment_count: int,
    viewer: User | None = None,
    agent: Agent | None = None,
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
        visibility=post.visibility,
        is_pinned=post.is_pinned,
        created_at=post.created_at,
        updated_at=post.updated_at,
        author=author_info,
        comment_count=comment_count,
        can_edit=can_manage,
        can_delete=can_manage,
    )


@router.get("", response_model=list[PostOut])
async def list_posts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    department: str | None = Query(None),
    category: str | None = Query(None),
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    offset = (page - 1) * page_size
    is_admin_view = bool(current_user and current_user.is_admin)
    stmt = select(Post)
    if not is_admin_view:
        stmt = stmt.where(Post.visibility == VISIBILITY_NORMAL, Post.is_deleted == False)  # noqa: E712
    if not category and not is_admin_view:
        stmt = stmt.where(Post.category != "公告")
    if department:
        stmt = stmt.where(Post.department_tag == department)
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

    return [
        _post_to_out(
            p,
            users.get(p.author_id) if p.author_id is not None else None,
            counts.get(p.id, 0),
            current_user,
            agents.get(p.agent_id) if p.agent_id is not None else None,
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

    post = Post(
        author_id=current_user.id,
        title=title,
        content=content,
        is_anonymous=body.is_anonymous,
        department_tag=body.department_tag.strip() if body.department_tag else None,
        category=_normalize_category(body.category, current_user.is_admin),
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
    return _post_to_out(post, current_user, 1 if yutoko_comment else 0)


@router.get("/{post_id}", response_model=PostOut)
async def get_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    is_admin_view = bool(current_user and current_user.is_admin)
    stmt = select(Post).where(Post.id == post_id)
    if not is_admin_view:
        stmt = stmt.where(Post.visibility == VISIBILITY_NORMAL, Post.is_deleted == False)  # noqa: E712
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    author = None
    agent = None
    if post.author_id is not None:
        author_result = await db.execute(select(User).where(User.id == post.author_id))
        author = author_result.scalar_one()
    if post.agent_id is not None:
        agent_result = await db.execute(select(Agent).where(Agent.id == post.agent_id))
        agent = agent_result.scalar_one()

    count_result = await db.execute(
        select(func.count(Comment.id)).where(
            Comment.post_id == post_id,
            Comment.visibility == VISIBILITY_NORMAL,
            Comment.is_deleted == False,  # noqa: E712
        )
    )
    count = count_result.scalar_one()

    return _post_to_out(post, author, count, current_user, agent)


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
    if body.category is not None:
        post.category = _normalize_category(body.category, current_user.is_admin)
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
    if post.agent_id is not None:
        agent_result = await db.execute(select(Agent).where(Agent.id == post.agent_id))
        agent = agent_result.scalar_one()
    count_result = await db.execute(
        select(func.count(Comment.id)).where(
            Comment.post_id == post_id,
            Comment.visibility == VISIBILITY_NORMAL,
            Comment.is_deleted == False,  # noqa: E712
        )
    )
    return _post_to_out(post, author, count_result.scalar_one(), current_user, agent)


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
