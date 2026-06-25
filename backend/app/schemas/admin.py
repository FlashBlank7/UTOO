from datetime import datetime
from pydantic import BaseModel


class CodeOut(BaseModel):
    id: int
    code: str
    max_uses: int
    use_count: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CodeUsageOut(BaseModel):
    user_id: int
    username: str | None
    display_name: str | None = None
    department: str
    used_at: datetime

    model_config = {"from_attributes": True}


class GenerateCodeRequest(BaseModel):
    max_uses: int = 20


class PatchCodeRequest(BaseModel):
    is_active: bool | None = None
    max_uses: int | None = None


class ResetPasswordRequest(BaseModel):
    new_password: str


class CreateAnnouncementRequest(BaseModel):
    title: str
    content: str


class AgentOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    api_key_prefix: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_posted_at: datetime | None = None

    model_config = {"from_attributes": True}


class CreateAgentRequest(BaseModel):
    name: str
    description: str | None = None


class PatchAgentRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class AgentWithKeyOut(AgentOut):
    api_key: str
