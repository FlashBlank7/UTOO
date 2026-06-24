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
