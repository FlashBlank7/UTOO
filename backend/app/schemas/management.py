from datetime import datetime
from pydantic import BaseModel
from app.schemas.school import BoardOut, SchoolBrief


MODERATOR_APPLICATION_PENDING = "pending"
MODERATOR_APPLICATION_APPROVED = "approved"
MODERATOR_APPLICATION_REJECTED = "rejected"


class ModeratorApplicationCreate(BaseModel):
    board_id: int
    reason: str | None = None


class ModeratorApplicationPatch(BaseModel):
    status: str


class ModeratorApplicationOut(BaseModel):
    id: int
    applicant_id: int
    applicant_name: str | None = None
    school: SchoolBrief
    board: BoardOut
    reason: str | None = None
    status: str
    reviewed_by: int | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ManagementScopeOut(BaseModel):
    school: SchoolBrief
    boards: list[BoardOut]


class ManagementScopesOut(BaseModel):
    is_admin: bool
    scopes: list[ManagementScopeOut]
