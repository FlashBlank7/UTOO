from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas.post import CommentCreate, CommentOut, AuthorInfo
from app.dependencies import get_current_user, get_optional_current_user
from app.core.moderation import (
    VISIBILITY_DELETED,
    VISIBILITY_HIDDEN,
    VISIBILITY_NORMAL,
    contains_sensitive_word,
    create_sensitive_report,
    enforce_rate_limit,
    ensure_can_publish,
    set_comment_visibility,
)

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
            visibility=VISIBILITY_DELETED,
            is_deleted=True,
            deleted_at=comment.deleted_at,
            created_at=comment.created_at,
            author=AuthorInfo(display_name="已删除"),
            can_delete=False,
        )
    if comment.visibility == VISIBILITY_HIDDEN and not (viewer and viewer.is_admin):
        return CommentOut(
            id=comment.id,
            content="评论已隐藏",
            is_anonymous=True,
            parent_id=comment.parent_id,
            visibility=VISIBILITY_HIDDEN,
            is_deleted=False,
            deleted_at=comment.deleted_at,
            created_at=comment.created_at,
            author=AuthorInfo(display_name="已隐藏"),
            can_delete=False,
        )
    return CommentOut(
        id=comment.id,
        content=comment.content,
        is_anonymous=comment.is_anonymous,
        parent_id=comment.parent_id,
        visibility=comment.visibility,
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
    post_result = await db.execute(
        select(Post).where(
            Post.id == post_id,
            Post.visibility == VISIBILITY_NORMAL,
            Post.is_deleted == False,  # noqa: E712
        )
    )
    if not post_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    result = await db.execute(
        select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at.asc())
    )
    comments = result.scalars().all()
    if not (current_user and current_user.is_admin):
        comments = [c for c in comments if c.visibility == VISIBILITY_NORMAL and not c.is_deleted]
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
    ensure_can_publish(current_user)
    await enforce_rate_limit(db, "user", current_user.id, "comment", 15)

    post_result = await db.execute(
        select(Post).where(
            Post.id == post_id,
            Post.visibility == VISIBILITY_NORMAL,
            Post.is_deleted == False,  # noqa: E712
        )
    )
    if not post_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    if body.parent_id:
        parent_result = await db.execute(
            select(Comment).where(
                Comment.id == body.parent_id,
                Comment.post_id == post_id,
                Comment.visibility == VISIBILITY_NORMAL,
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
    if contains_sensitive_word(body.content):
        set_comment_visibility(comment, VISIBILITY_HIDDEN)
    db.add(comment)
    await db.flush()
    if comment.visibility == VISIBILITY_HIDDEN:
        await create_sensitive_report(db, "comment", comment.id, "Comment matched sensitive words")
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
    if comment.visibility == VISIBILITY_DELETED or comment.is_deleted:
        return
    if comment.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")

    set_comment_visibility(comment, VISIBILITY_DELETED)
    await db.commit()
