import secrets
import string
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.models.activation_code import ActivationCode, ActivationCodeUsage
from app.models.post import Post
from app.models.agent import Agent
from app.schemas.admin import (
    AgentOut,
    AgentWithKeyOut,
    CodeOut,
    CodeUsageOut,
    CreateAgentRequest,
    GenerateCodeRequest,
    PatchAgentRequest,
    PatchCodeRequest,
    ResetPasswordRequest,
)
from app.schemas.user import UserOut
from app.core.security import hash_password
from app.core.agent_keys import agent_key_prefix, generate_agent_api_key
from app.dependencies import get_current_admin

router = APIRouter()


def _random_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _agent_response_with_key(agent: Agent, api_key: str) -> AgentWithKeyOut:
    return AgentWithKeyOut(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        api_key_prefix=agent.api_key_prefix,
        api_key=api_key,
        is_active=agent.is_active,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        last_posted_at=agent.last_posted_at,
    )


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


@router.get("/agents", response_model=list[AgentOut])
async def list_agents(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Agent).order_by(Agent.created_at.desc()))
    return result.scalars().all()


@router.post("/agents", response_model=AgentWithKeyOut, status_code=status.HTTP_201_CREATED)
async def create_agent(
    body: CreateAgentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Agent name is required")

    exists = await db.execute(select(Agent).where(Agent.name == name))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Agent name already exists")

    api_key = generate_agent_api_key()
    agent = Agent(
        name=name,
        description=body.description.strip() if body.description else None,
        api_key_prefix=agent_key_prefix(api_key),
        api_key_hash=hash_password(api_key),
        created_by=current_user.id,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return _agent_response_with_key(agent, api_key)


@router.patch("/agents/{agent_id}", response_model=AgentOut)
async def patch_agent(
    agent_id: int,
    body: PatchAgentRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Agent name is required")
        exists = await db.execute(select(Agent).where(Agent.name == name, Agent.id != agent.id))
        if exists.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Agent name already exists")
        agent.name = name
    if "description" in body.model_fields_set:
        agent.description = body.description.strip() if body.description else None
    if body.is_active is not None:
        agent.is_active = body.is_active

    await db.commit()
    await db.refresh(agent)
    return agent


@router.post("/agents/{agent_id}/reset-key", response_model=AgentWithKeyOut)
async def reset_agent_key(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    api_key = generate_agent_api_key()
    agent.api_key_prefix = agent_key_prefix(api_key)
    agent.api_key_hash = hash_password(api_key)
    await db.commit()
    await db.refresh(agent)
    return _agent_response_with_key(agent, api_key)


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
    post.is_deleted = True
    post.deleted_at = datetime.now(timezone.utc)
    await db.commit()


@router.patch("/users/{user_id}/password", response_model=UserOut)
async def reset_user_password(
    user_id: int,
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(body.new_password)
    await db.commit()
    await db.refresh(user)
    return user
