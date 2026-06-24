from datetime import datetime
from pydantic import BaseModel


class AuthorInfo(BaseModel):
    display_name: str
    department: str | None = None
    source: str = "user"
    id: int | None = None


class PostCreate(BaseModel):
    title: str
    content: str
    is_anonymous: bool = False
    department_tag: str | None = None
    category: str = "闲聊"


class PostUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    department_tag: str | None = None
    category: str | None = None
    is_pinned: bool | None = None


class PostOut(BaseModel):
    id: int
    title: str
    content: str
    is_anonymous: bool
    department_tag: str | None
    category: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
    author: AuthorInfo
    comment_count: int = 0
    can_edit: bool = False
    can_delete: bool = False

    model_config = {"from_attributes": True}


class CommentCreate(BaseModel):
    content: str
    is_anonymous: bool = False
    parent_id: int | None = None


class CommentOut(BaseModel):
    id: int
    content: str
    is_anonymous: bool
    parent_id: int | None
    is_deleted: bool = False
    deleted_at: datetime | None = None
    created_at: datetime
    author: AuthorInfo
    can_delete: bool = False

    model_config = {"from_attributes": True}
