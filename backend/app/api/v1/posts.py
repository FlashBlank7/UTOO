from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.db.session import get_db
from app.models.post import Post
from app.models.user import User
from app.models.comment import Comment
from app.schemas.post import PostCreate, PostOut, PostUpdate, AuthorInfo
from app.dependencies import get_current_user, get_optional_current_user

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
        return AuthorInfo(display_name=ANON_DISPLAY)
    return AuthorInfo(display_name=user.display_name or f"用户{user.id}", department=user.department)


def _can_manage(post: Post, user: User | None) -> bool:
    return bool(user and (user.is_admin or post.author_id == user.id))


def _post_to_out(post: Post, author: User, comment_count: int, viewer: User | None = None) -> PostOut:
    can_manage = _can_manage(post, viewer)
    return PostOut(
        id=post.id,
        title=post.title,
        content=post.content,
        is_anonymous=post.is_anonymous,
        department_tag=post.department_tag,
        category=post.category,
        is_pinned=post.is_pinned,
        created_at=post.created_at,
        updated_at=post.updated_at,
        author=_author_info(author, post.is_anonymous),
        comment_count=comment_count,
        can_edit=can_manage,
        can_delete=can_manage,
    )


@router.get("", response_model=list[PostOut])
async def list_posts(
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
    department: str | None = Query(None),
    category: str | None = Query(None),
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    offset = (page - 1) * page_size
    stmt = select(Post).where(Post.is_deleted == False)  # noqa: E712
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

    author_ids = [p.author_id for p in posts]
    users_result = await db.execute(select(User).where(User.id.in_(author_ids)))
    users = {u.id: u for u in users_result.scalars().all()}

    post_ids = [p.id for p in posts]
    counts_result = await db.execute(
        select(Comment.post_id, func.count(Comment.id))
        .where(Comment.post_id.in_(post_ids), Comment.is_deleted == False)  # noqa: E712
        .group_by(Comment.post_id)
    )
    counts = {row[0]: row[1] for row in counts_result.all()}

    return [_post_to_out(p, users[p.author_id], counts.get(p.id, 0), current_user) for p in posts]


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

    post = Post(
        author_id=current_user.id,
        title=title,
        content=content,
        is_anonymous=body.is_anonymous,
        department_tag=body.department_tag.strip() if body.department_tag else None,
        category=_normalize_category(body.category, current_user.is_admin),
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return _post_to_out(post, current_user, 0)


@router.get("/{post_id}", response_model=PostOut)
async def get_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id, Post.is_deleted == False))  # noqa: E712
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    author_result = await db.execute(select(User).where(User.id == post.author_id))
    author = author_result.scalar_one()

    count_result = await db.execute(
        select(func.count(Comment.id)).where(Comment.post_id == post_id, Comment.is_deleted == False)  # noqa: E712
    )
    count = count_result.scalar_one()

    return _post_to_out(post, author, count, current_user)


@router.patch("/{post_id}", response_model=PostOut)
async def update_post(
    post_id: int,
    body: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id, Post.is_deleted == False))  # noqa: E712
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

    await db.commit()
    await db.refresh(post)

    author_result = await db.execute(select(User).where(User.id == post.author_id))
    author = author_result.scalar_one()
    count_result = await db.execute(
        select(func.count(Comment.id)).where(Comment.post_id == post_id, Comment.is_deleted == False)  # noqa: E712
    )
    return _post_to_out(post, author, count_result.scalar_one(), current_user)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id, Post.is_deleted == False))  # noqa: E712
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")
    post.is_deleted = True
    post.deleted_at = datetime.now(timezone.utc)
    await db.commit()
