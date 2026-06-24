from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas.post import CommentCreate, CommentOut, AuthorInfo
from app.dependencies import get_current_user, get_optional_current_user

router = APIRouter()

ANON_DISPLAY = "匿名用户"


def _author_info(user: User, is_anonymous: bool) -> AuthorInfo:
    if is_anonymous:
        return AuthorInfo(display_name=ANON_DISPLAY)
    return AuthorInfo(display_name=user.display_name or f"用户{user.id}", department=user.department)


def _comment_to_out(comment: Comment, author: User, viewer: User | None = None) -> CommentOut:
    can_delete = bool(viewer and (viewer.is_admin or comment.author_id == viewer.id))
    if comment.is_deleted:
        return CommentOut(
            id=comment.id,
            content="评论已删除",
            is_anonymous=True,
            parent_id=comment.parent_id,
            is_deleted=True,
            deleted_at=comment.deleted_at,
            created_at=comment.created_at,
            author=AuthorInfo(display_name="已删除"),
            can_delete=False,
        )
    return CommentOut(
        id=comment.id,
        content=comment.content,
        is_anonymous=comment.is_anonymous,
        parent_id=comment.parent_id,
        is_deleted=False,
        deleted_at=comment.deleted_at,
        created_at=comment.created_at,
        author=_author_info(author, comment.is_anonymous),
        can_delete=can_delete,
    )


@router.get("/post/{post_id}", response_model=list[CommentOut])
async def list_comments(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    post_result = await db.execute(select(Post).where(Post.id == post_id, Post.is_deleted == False))  # noqa: E712
    if not post_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

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
        _comment_to_out(c, users[c.author_id], current_user)
        for c in comments
    ]


@router.post("/post/{post_id}", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: int,
    body: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post_result = await db.execute(select(Post).where(Post.id == post_id, Post.is_deleted == False))  # noqa: E712
    if not post_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    if body.parent_id:
        parent_result = await db.execute(
            select(Comment).where(
                Comment.id == body.parent_id,
                Comment.post_id == post_id,
                Comment.is_deleted == False,  # noqa: E712
            )
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

    return _comment_to_out(comment, current_user, current_user)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.is_deleted:
        return
    if comment.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")

    comment.is_deleted = True
    comment.deleted_at = datetime.now(timezone.utc)
    await db.commit()
