from datetime import datetime
from pydantic import BaseModel


class ReportCreate(BaseModel):
    target_type: str
    target_id: int
    reason: str
    details: str | None = None


class ReportOut(BaseModel):
    id: int
    reporter_id: int | None
    target_type: str
    target_id: int
    reason: str
    details: str | None = None
    status: str
    resolved_by: int | None = None
    resolution: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PatchReportRequest(BaseModel):
    action: str = "resolve"
    resolution: str | None = None
    mute_days: int | None = None


class VisibilityRequest(BaseModel):
    visibility: str
    reason: str | None = None


class UserModerationRequest(BaseModel):
    is_banned: bool | None = None
    mute_days: int | None = None
    clear_mute: bool = False
    reason: str | None = None


class ModerationLogOut(BaseModel):
    id: int
    admin_id: int
    target_type: str
    target_id: int
    action: str
    reason: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
