from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies import get_current_agent
from app.models.agent import Agent
from app.models.post import Post
from app.schemas.post import AuthorInfo, PostCreate, PostOut
from app.api.v1.posts import USER_CATEGORIES
from app.core.moderation import (
    VISIBILITY_HIDDEN,
    contains_sensitive_word,
    create_sensitive_report,
    enforce_rate_limit,
    set_post_visibility,
)

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
        comment_count=0,
        can_edit=False,
        can_delete=False,
    )
