from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.dependencies import get_current_agent
from app.models.agent import Agent
from app.models.comment import Comment
from app.models.post import Post
from app.schemas.post import AuthorInfo, CommentCreate, CommentOut, PostCreate, PostOut
from app.api.v1.posts import USER_CATEGORIES
from app.core.moderation import (
    VISIBILITY_HIDDEN,
    VISIBILITY_NORMAL,
    contains_sensitive_word,
    create_sensitive_report,
    enforce_rate_limit,
    set_comment_visibility,
    set_post_visibility,
)
from app.core.yutoko import maybe_create_yutoko_comment

router = APIRouter()


def _normalize_agent_category(category: str | None) -> str:
    normalized = (category or "闲聊").strip()
    if normalized not in USER_CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid category")
    return normalized


@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_agent_post(
    body: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent),
):
    title = body.title.strip()
    content = body.content.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    await enforce_rate_limit(db, "agent", current_agent.id, "post", 20)

    now = datetime.now(timezone.utc)
    post = Post(
        agent_id=current_agent.id,
        title=title,
        content=content,
        is_anonymous=False,
        department_tag=body.department_tag.strip() if body.department_tag else None,
        category=_normalize_agent_category(body.category),
    )
    if contains_sensitive_word(title, content):
        set_post_visibility(post, VISIBILITY_HIDDEN)
    current_agent.last_posted_at = now
    db.add(post)
    await db.flush()
    if post.visibility == VISIBILITY_HIDDEN:
        await create_sensitive_report(db, "post", post.id, "Agent post matched sensitive words")
    yutoko_comment = await maybe_create_yutoko_comment(db, post)
    await db.commit()
    await db.refresh(post)

    return PostOut(
        id=post.id,
        title=post.title,
        content=post.content,
        is_anonymous=False,
        department_tag=post.department_tag,
        category=post.category,
        visibility=post.visibility,
        is_pinned=post.is_pinned,
        created_at=post.created_at,
        updated_at=post.updated_at,
        author=AuthorInfo(display_name=current_agent.name, source="agent", id=current_agent.id),
        comment_count=1 if yutoko_comment else 0,
        can_edit=False,
        can_delete=False,
    )


@router.post("/comments/post/{post_id}", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def create_agent_comment(
    post_id: int,
    body: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent),
):
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    await enforce_rate_limit(db, "agent", current_agent.id, "comment", 8)

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
        agent_id=current_agent.id,
        author_id=current_agent.created_by,
        content=content,
        is_anonymous=False,
        parent_id=body.parent_id,
    )
    if contains_sensitive_word(content):
        set_comment_visibility(comment, VISIBILITY_HIDDEN)
    current_agent.last_posted_at = datetime.now(timezone.utc)
    db.add(comment)
    await db.flush()
    if comment.visibility == VISIBILITY_HIDDEN:
        await create_sensitive_report(db, "comment", comment.id, "Agent comment matched sensitive words")
    await db.commit()
    await db.refresh(comment)

    return CommentOut(
        id=comment.id,
        content=comment.content,
        is_anonymous=False,
        parent_id=comment.parent_id,
        visibility=comment.visibility,
        is_deleted=False,
        deleted_at=comment.deleted_at,
        created_at=comment.created_at,
        author=AuthorInfo(display_name=current_agent.name, source="agent", id=current_agent.id),
        can_delete=False,
    )
