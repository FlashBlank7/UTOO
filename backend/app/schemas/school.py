from datetime import datetime
from pydantic import BaseModel, Field


class SchoolOut(BaseModel):
    id: int
    slug: str
    name_zh: str
    name_en: str
    name_ja: str
    country: str
    kind: str
    rank_source: str | None = None
    rank_label: str | None = None
    rank_order: int | None = None
    theme: str
    description: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class SchoolBrief(BaseModel):
    id: int
    slug: str
    name_zh: str
    name_en: str
    name_ja: str
    kind: str = "real"
    theme: str = "standard"
    description: str | None = None

    model_config = {"from_attributes": True}


class BoardOut(BaseModel):
    id: int
    school_id: int
    parent_id: int | None = None
    slug: str
    name: str
    description: str | None = None
    status: str
    sort_order: int
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime
    school: SchoolBrief | None = None
    parent_name: str | None = None
    children: list["BoardOut"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class BoardCreateRequest(BaseModel):
    school_id: int | None = None
    school_slug: str | None = None
    parent_id: int | None = None
    name: str
    description: str | None = None


class BoardPatchRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    sort_order: int | None = None


class SchoolPatchRequest(BaseModel):
    description: str | None = None


class SchoolMatchOut(BaseModel):
    matched: bool
    school: SchoolBrief | None = None
    custom_name: str | None = None


class SchoolRequestCreate(BaseModel):
    name_zh: str
    name_en: str | None = None
    name_ja: str | None = None
    aliases: str | None = None
    website: str | None = None
    description: str | None = None


class SchoolRequestPatch(BaseModel):
    status: str


class SchoolRequestOut(BaseModel):
    id: int
    requested_by: int
    name_zh: str
    name_en: str | None = None
    name_ja: str | None = None
    aliases: str | None = None
    website: str | None = None
    description: str | None = None
    status: str
    created_school: SchoolBrief | None = None
    created_school_id: int | None = None
    reviewed_by: int | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
