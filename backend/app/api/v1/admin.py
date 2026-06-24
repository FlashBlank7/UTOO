import secrets
import string
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.models.activation_code import ActivationCode, ActivationCodeUsage
from app.models.post import Post
from app.schemas.admin import CodeOut, CodeUsageOut, GenerateCodeRequest, PatchCodeRequest
from app.schemas.user import UserOut
from app.dependencies import get_current_admin

router = APIRouter()


def _random_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@router.get("/codes", response_model=list[CodeOut])
async def list_codes(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(ActivationCode).order_by(ActivationCode.created_at.desc()))
    return result.scalars().all()


@router.post("/codes", response_model=CodeOut, status_code=status.HTTP_201_CREATED)
async def generate_code(
    body: GenerateCodeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    code = ActivationCode(code=_random_code(), created_by=current_user.id, max_uses=body.max_uses)
    db.add(code)
    await db.commit()
    await db.refresh(code)
    return code


@router.get("/codes/{code_id}/usages", response_model=list[CodeUsageOut])
async def code_usages(
    code_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(ActivationCodeUsage).where(ActivationCodeUsage.code_id == code_id)
    )
    usages = result.scalars().all()
    if not usages:
        return []

    user_ids = [u.user_id for u in usages]
    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users = {u.id: u for u in users_result.scalars().all()}

    return [
        CodeUsageOut(
            user_id=u.user_id,
            username=users[u.user_id].username,
            display_name=users[u.user_id].display_name,
            department=users[u.user_id].department,
            used_at=u.used_at,
        )
        for u in usages
    ]


@router.patch("/codes/{code_id}", response_model=CodeOut)
async def patch_code(
    code_id: int,
    body: PatchCodeRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(ActivationCode).where(ActivationCode.id == code_id))
    code = result.scalar_one_or_none()
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")
    if body.is_active is not None:
        code.is_active = body.is_active
    if body.max_uses is not None:
        code.max_uses = body.max_uses
    await db.commit()
    await db.refresh(code)
    return code


@router.get("/users", response_model=list[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    await db.delete(post)
    await db.commit()
