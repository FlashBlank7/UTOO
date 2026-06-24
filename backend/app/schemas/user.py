from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: int
    username: str | None
    display_name: str | None = None
    department: str
    email: EmailStr | None = None
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    activation_code: str
    password: str
    department: str
    username: str
    display_name: str | None = None
    email: EmailStr | None = None


class LoginRequest(BaseModel):
    password: str
    username: str | None = None
    email: EmailStr | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class UpdateMeRequest(BaseModel):
    display_name: str | None = None
    department: str | None = None
    email: EmailStr | None = None
    current_password: str | None = None
    new_password: str | None = None
