from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.moderation import REPORT_PENDING, VISIBILITY_NORMAL
from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.comment import Comment
from app.models.post import Post
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportCreate, ReportOut

router = APIRouter()


async def _ensure_report_target(db: AsyncSession, target_type: str, target_id: int) -> None:
    if target_type == "post":
        result = await db.execute(
            select(Post).where(Post.id == target_id, Post.visibility == VISIBILITY_NORMAL)
        )
    elif target_type == "comment":
        result = await db.execute(
            select(Comment).where(Comment.id == target_id, Comment.visibility == VISIBILITY_NORMAL)
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid target type")

    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Report target not found")


@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
async def create_report(
    body: ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_type = body.target_type.strip()
    reason = body.reason.strip()
    if not reason:
        raise HTTPException(status_code=400, detail="Reason is required")
    await _ensure_report_target(db, target_type, body.target_id)

    existing = await db.execute(
        select(Report).where(
            Report.reporter_id == current_user.id,
            Report.target_type == target_type,
            Report.target_id == body.target_id,
            Report.status == REPORT_PENDING,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Report already submitted")

    report = Report(
        reporter_id=current_user.id,
        target_type=target_type,
        target_id=body.target_id,
        reason=reason,
        details=body.details.strip() if body.details else None,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report
