import secrets
import string
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError
from app.db.session import get_db
from app.models.user import User
from app.models.activation_code import ActivationCode, ActivationCodeUsage
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.schemas.user import RegisterRequest, LoginRequest, RefreshRequest, TokenResponse, UserOut
from app.dependencies import get_current_user

router = APIRouter()

ADMIN_BOOTSTRAP_CODE = "UTOO-ADMIN"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    is_admin = False
    if body.activation_code == ADMIN_BOOTSTRAP_CODE:
        result = await db.execute(select(User).where(User.is_admin == True))  # noqa: E712
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Admin bootstrap code already used")
        is_admin = True
        activation_code_record = None
    else:
        result = await db.execute(
            select(ActivationCode).where(
                ActivationCode.code == body.activation_code,
                ActivationCode.is_active == True,  # noqa: E712
            )
        )
        activation_code_record = result.scalar_one_or_none()
        if not activation_code_record:
            raise HTTPException(status_code=400, detail="Invalid or inactive activation code")
        if activation_code_record.use_count >= activation_code_record.max_uses:
            raise HTTPException(status_code=400, detail="Activation code has reached its usage limit")

    if body.username:
        exists = await db.execute(select(User).where(User.username == body.username))
        if exists.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already taken")
    if body.email:
        exists = await db.execute(select(User).where(User.email == str(body.email)))
        if exists.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        department=body.department,
        email=str(body.email) if body.email else None,
        is_admin=is_admin,
    )
    db.add(user)
    await db.flush()

    if activation_code_record:
        activation_code_record.use_count += 1
        if activation_code_record.use_count >= activation_code_record.max_uses:
            activation_code_record.is_active = False
        db.add(ActivationCodeUsage(code_id=activation_code_record.id, user_id=user.id))

    await db.commit()
    return TokenResponse(access_token=create_access_token(user.id), refresh_token=create_refresh_token(user.id))


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    if not body.username and not body.email:
        raise HTTPException(status_code=400, detail="Provide username or email")

    if body.username:
        result = await db.execute(select(User).where(User.username == body.username))
    else:
        result = await db.execute(select(User).where(User.email == str(body.email)))

    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return TokenResponse(access_token=create_access_token(user.id), refresh_token=create_refresh_token(user.id))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError
        user_id = int(payload["sub"])
    except (JWTError, ValueError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return TokenResponse(access_token=create_access_token(user.id), refresh_token=create_refresh_token(user.id))


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
