from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas.post import CommentCreate, CommentOut, AuthorInfo
from app.dependencies import get_current_user

router = APIRouter()

ANON_DISPLAY = "匿名用户"


def _author_info(user: User, is_anonymous: bool) -> AuthorInfo:
    if is_anonymous:
        return AuthorInfo(display_name=ANON_DISPLAY)
    return AuthorInfo(display_name=user.username or f"用户{user.id}", department=user.department)


@router.get("/post/{post_id}", response_model=list[CommentOut])
async def list_comments(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at.asc())
    )
    comments = result.scalars().all()
    if not comments:
        return []

    author_ids = list({c.author_id for c in comments})
    users_result = await db.execute(select(User).where(User.id.in_(author_ids)))
    users = {u.id: u for u in users_result.scalars().all()}

    return [
        CommentOut(
            id=c.id,
            content=c.content,
            is_anonymous=c.is_anonymous,
            parent_id=c.parent_id,
            created_at=c.created_at,
            author=_author_info(users[c.author_id], c.is_anonymous),
        )
        for c in comments
    ]


@router.post("/post/{post_id}", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: int,
    body: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post_result = await db.execute(select(Post).where(Post.id == post_id))
    if not post_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    if body.parent_id:
        parent_result = await db.execute(
            select(Comment).where(Comment.id == body.parent_id, Comment.post_id == post_id)
        )
        if not parent_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Parent comment not found")

    comment = Comment(
        post_id=post_id,
        author_id=current_user.id,
        content=body.content,
        is_anonymous=body.is_anonymous,
        parent_id=body.parent_id,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return CommentOut(
        id=comment.id,
        content=comment.content,
        is_anonymous=comment.is_anonymous,
        parent_id=comment.parent_id,
        created_at=comment.created_at,
        author=_author_info(current_user, comment.is_anonymous),
    )
