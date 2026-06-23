from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.post import Post
from app.models.user import User
from app.models.comment import Comment
from app.schemas.post import PostCreate, PostOut, AuthorInfo
from app.dependencies import get_current_user

router = APIRouter()

ANON_DISPLAY = "匿名用户"


def _author_info(user: User, is_anonymous: bool) -> AuthorInfo:
    if is_anonymous:
        return AuthorInfo(display_name=ANON_DISPLAY)
    return AuthorInfo(display_name=user.username or f"用户{user.id}", department=user.department)


def _post_to_out(post: Post, author: User, comment_count: int) -> PostOut:
    return PostOut(
        id=post.id,
        title=post.title,
        content=post.content,
        is_anonymous=post.is_anonymous,
        department_tag=post.department_tag,
        created_at=post.created_at,
        author=_author_info(author, post.is_anonymous),
        comment_count=comment_count,
    )


@router.get("", response_model=list[PostOut])
async def list_posts(
    db: AsyncSession = Depends(get_db),
    department: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    offset = (page - 1) * page_size
    stmt = select(Post).order_by(Post.created_at.desc()).offset(offset).limit(page_size)
    if department:
        stmt = stmt.where(Post.department_tag == department)

    result = await db.execute(stmt)
    posts = result.scalars().all()

    if not posts:
        return []

    author_ids = [p.author_id for p in posts]
    users_result = await db.execute(select(User).where(User.id.in_(author_ids)))
    users = {u.id: u for u in users_result.scalars().all()}

    post_ids = [p.id for p in posts]
    counts_result = await db.execute(
        select(Comment.post_id, func.count(Comment.id)).where(Comment.post_id.in_(post_ids)).group_by(Comment.post_id)
    )
    counts = {row[0]: row[1] for row in counts_result.all()}

    return [_post_to_out(p, users[p.author_id], counts.get(p.id, 0)) for p in posts]


@router.post("", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(
    body: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = Post(
        author_id=current_user.id,
        title=body.title,
        content=body.content,
        is_anonymous=body.is_anonymous,
        department_tag=body.department_tag,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return _post_to_out(post, current_user, 0)


@router.get("/{post_id}", response_model=PostOut)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    author_result = await db.execute(select(User).where(User.id == post.author_id))
    author = author_result.scalar_one()

    count_result = await db.execute(select(func.count(Comment.id)).where(Comment.post_id == post_id))
    count = count_result.scalar_one()

    return _post_to_out(post, author, count)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")
    await db.delete(post)
    await db.commit()
