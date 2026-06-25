from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.comment import Comment
from app.models.post import Post
from app.models.report import ModerationLog, RateLimitEvent, Report
from app.models.user import User

VISIBILITY_NORMAL = "normal"
VISIBILITY_HIDDEN = "hidden"
VISIBILITY_DELETED = "deleted"
REPORT_PENDING = "pending"
REPORT_RESOLVED = "resolved"
SENSITIVE_WORDS = ("诈骗", "博彩", "代写", "裸聊", "办证")


def contains_sensitive_word(*parts: str | None) -> bool:
    text = "\n".join(part or "" for part in parts).lower()
    return any(word.lower() in text for word in SENSITIVE_WORDS)


def is_muted(user: User) -> bool:
    if not user.muted_until:
        return False
    muted_until = user.muted_until
    if muted_until.tzinfo is None:
        muted_until = muted_until.replace(tzinfo=timezone.utc)
    return muted_until > datetime.now(timezone.utc)


def ensure_can_publish(user: User) -> None:
    if user.is_banned:
        raise HTTPException(status_code=403, detail="Account is banned")
    if is_muted(user):
        raise HTTPException(status_code=403, detail="Account is muted")


async def enforce_rate_limit(
    db: AsyncSession,
    actor_type: str,
    actor_id: int,
    action: str,
    seconds: int,
) -> None:
    since = datetime.now(timezone.utc) - timedelta(seconds=seconds)
    result = await db.execute(
        select(func.count(RateLimitEvent.id)).where(
            RateLimitEvent.actor_type == actor_type,
            RateLimitEvent.actor_id == actor_id,
            RateLimitEvent.action == action,
            RateLimitEvent.created_at >= since,
        )
    )
    if result.scalar_one() > 0:
        raise HTTPException(status_code=429, detail="Too many requests, please wait")
    db.add(RateLimitEvent(actor_type=actor_type, actor_id=actor_id, action=action))


async def create_sensitive_report(
    db: AsyncSession,
    target_type: str,
    target_id: int,
    details: str,
) -> None:
    db.add(
        Report(
            reporter_id=None,
            target_type=target_type,
            target_id=target_id,
            reason="sensitive_word",
            details=details,
            status=REPORT_PENDING,
        )
    )


def set_post_visibility(post: Post, visibility: str) -> None:
    post.visibility = visibility
    post.is_deleted = visibility == VISIBILITY_DELETED
    if visibility == VISIBILITY_DELETED and not post.deleted_at:
        post.deleted_at = datetime.now(timezone.utc)


def set_comment_visibility(comment: Comment, visibility: str) -> None:
    comment.visibility = visibility
    comment.is_deleted = visibility == VISIBILITY_DELETED
    if visibility == VISIBILITY_DELETED and not comment.deleted_at:
        comment.deleted_at = datetime.now(timezone.utc)


def add_moderation_log(
    db: AsyncSession,
    admin: User,
    target_type: str,
    target_id: int,
    action: str,
    reason: str | None = None,
) -> None:
    db.add(
        ModerationLog(
            admin_id=admin.id,
            target_type=target_type,
            target_id=target_id,
            action=action,
            reason=reason,
        )
    )
