from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.school import Board, ModeratorApplication, School, SchoolModerator
from app.models.user import User
from app.schemas.management import (
    MODERATOR_APPLICATION_PENDING,
    ModeratorApplicationCreate,
    ModeratorApplicationOut,
)
from app.schemas.school import BoardOut, SchoolBrief
from app.core.schools import BOARD_STATUS_APPROVED

router = APIRouter()


def _school_brief(school: School) -> SchoolBrief:
    return SchoolBrief(
        id=school.id,
        slug=school.slug,
        name_zh=school.name_zh,
        name_en=school.name_en,
        name_ja=school.name_ja,
        kind=school.kind,
        theme=school.theme,
        description=school.description,
    )


def _board_out(board: Board, school: School) -> BoardOut:
    return BoardOut(
        id=board.id,
        school_id=board.school_id,
        parent_id=board.parent_id,
        slug=board.slug,
        name=board.name,
        description=board.description,
        status=board.status,
        sort_order=board.sort_order,
        created_by=board.created_by,
        created_at=board.created_at,
        updated_at=board.updated_at,
        school=_school_brief(school),
    )


def _application_out(application: ModeratorApplication, school: School, board: Board, applicant: User | None = None) -> ModeratorApplicationOut:
    return ModeratorApplicationOut(
        id=application.id,
        applicant_id=application.applicant_id,
        applicant_name=(applicant.display_name or applicant.username) if applicant else None,
        school=_school_brief(school),
        board=_board_out(board, school),
        reason=application.reason,
        status=application.status,
        reviewed_by=application.reviewed_by,
        reviewed_at=application.reviewed_at,
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


@router.post("", response_model=ModeratorApplicationOut, status_code=status.HTTP_201_CREATED)
async def create_moderator_application(
    body: ModeratorApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    board_result = await db.execute(select(Board).where(Board.id == body.board_id, Board.status == BOARD_STATUS_APPROVED))
    board = board_result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    school_result = await db.execute(select(School).where(School.id == board.school_id, School.is_active == True))  # noqa: E712
    school = school_result.scalar_one_or_none()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    existing_moderator = await db.execute(
        select(SchoolModerator.id).where(
            SchoolModerator.user_id == current_user.id,
            SchoolModerator.school_id == school.id,
            SchoolModerator.is_active == True,  # noqa: E712
        )
    )
    if existing_moderator.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already a moderator for this school")

    existing_pending = await db.execute(
        select(ModeratorApplication.id).where(
            ModeratorApplication.applicant_id == current_user.id,
            ModeratorApplication.school_id == school.id,
            ModeratorApplication.status == MODERATOR_APPLICATION_PENDING,
        )
    )
    if existing_pending.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Moderator application already pending")

    application = ModeratorApplication(
        applicant_id=current_user.id,
        school_id=school.id,
        board_id=board.id,
        reason=body.reason.strip() if body.reason else None,
        status=MODERATOR_APPLICATION_PENDING,
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return _application_out(application, school, board, current_user)


@router.get("/me", response_model=list[ModeratorApplicationOut])
async def list_my_moderator_applications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ModeratorApplication).where(ModeratorApplication.applicant_id == current_user.id).order_by(ModeratorApplication.created_at.desc())
    )
    applications = result.scalars().all()
    if not applications:
        return []
    school_ids = {application.school_id for application in applications}
    board_ids = {application.board_id for application in applications}
    school_result = await db.execute(select(School).where(School.id.in_(school_ids)))
    board_result = await db.execute(select(Board).where(Board.id.in_(board_ids)))
    schools = {school.id: school for school in school_result.scalars().all()}
    boards = {board.id: board for board in board_result.scalars().all()}
    return [
        _application_out(application, schools[application.school_id], boards[application.board_id], current_user)
        for application in applications
        if application.school_id in schools and application.board_id in boards
    ]
