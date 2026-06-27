from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.school import SchoolRequest
from app.models.user import User
from app.schemas.school import SchoolRequestCreate, SchoolRequestOut
from app.core.schools import SCHOOL_REQUEST_PENDING

router = APIRouter()


@router.post("", response_model=SchoolRequestOut, status_code=status.HTTP_201_CREATED)
async def request_school(
    body: SchoolRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    name_zh = body.name_zh.strip()
    if not name_zh:
        raise HTTPException(status_code=400, detail="School name is required")

    duplicate = await db.execute(
        select(SchoolRequest).where(
            SchoolRequest.requested_by == current_user.id,
            SchoolRequest.name_zh == name_zh,
            SchoolRequest.status == SCHOOL_REQUEST_PENDING,
        )
    )
    if duplicate.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="School request already pending")

    request = SchoolRequest(
        requested_by=current_user.id,
        name_zh=name_zh,
        name_en=body.name_en.strip() if body.name_en else None,
        name_ja=body.name_ja.strip() if body.name_ja else None,
        aliases=body.aliases.strip() if body.aliases else None,
        website=body.website.strip() if body.website else None,
        description=body.description.strip() if body.description else None,
        status=SCHOOL_REQUEST_PENDING,
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)
    return request
