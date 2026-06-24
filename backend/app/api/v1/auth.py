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
from app.schemas.user import RegisterRequest, LoginRequest, RefreshRequest, TokenResponse, UserOut, UpdateMeRequest
from app.dependencies import get_current_user

router = APIRouter()

ADMIN_BOOTSTRAP_CODE = "UTOO-ADMIN"


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    username = body.username.strip()
    display_name = body.display_name.strip() if body.display_name else None
    department = body.department.strip()

    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    if not department:
        raise HTTPException(status_code=400, detail="Department is required")

    is_admin = False
    if body.activation_code == ADMIN_BOOTSTRAP_CODE:
        result = await db.execute(select(User).where(User.is_admin == True))  # noqa: E712
        existing_admin = result.scalar_one_or_none()
        if existing_admin and existing_admin.username:
            raise HTTPException(status_code=400, detail="Admin bootstrap code already used")
        if existing_admin:
            exists = await db.execute(select(User).where(User.username == username))
            if exists.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Username already taken")
            if body.email:
                email = str(body.email)
                exists = await db.execute(select(User).where(User.email == email, User.id != existing_admin.id))
                if exists.scalar_one_or_none():
                    raise HTTPException(status_code=400, detail="Email already registered")

            existing_admin.username = username
            existing_admin.display_name = display_name
            existing_admin.hashed_password = hash_password(body.password)
            existing_admin.department = department
            existing_admin.email = str(body.email) if body.email else None
            await db.commit()
            await db.refresh(existing_admin)
            return TokenResponse(
                access_token=create_access_token(existing_admin.id),
                refresh_token=create_refresh_token(existing_admin.id),
            )
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

    exists = await db.execute(select(User).where(User.username == username))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already taken")
    if body.email:
        exists = await db.execute(select(User).where(User.email == str(body.email)))
        if exists.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=username,
        display_name=display_name,
        hashed_password=hash_password(body.password),
        department=department,
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
        result = await db.execute(select(User).where(User.username == body.username.strip()))
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


@router.patch("/me", response_model=UserOut)
async def update_me(
    body: UpdateMeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if "display_name" in body.model_fields_set:
        display_name = body.display_name.strip() if body.display_name else None
        current_user.display_name = display_name or None

    if body.department is not None:
        department = body.department.strip()
        if not department:
            raise HTTPException(status_code=400, detail="Department is required")
        current_user.department = department

    if "email" in body.model_fields_set:
        email = str(body.email) if body.email else None
        if email and email != current_user.email:
            exists = await db.execute(select(User).where(User.email == email))
            if exists.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Email already registered")
        current_user.email = email

    if body.new_password is not None:
        if not body.current_password:
            raise HTTPException(status_code=400, detail="Current password is required")
        if not verify_password(body.current_password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        if len(body.new_password) < 6:
            raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
        current_user.hashed_password = hash_password(body.new_password)

    await db.commit()
    await db.refresh(current_user)
    return current_user
