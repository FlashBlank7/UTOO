from datetime import datetime
from pydantic import BaseModel


class AuthorInfo(BaseModel):
    display_name: str
    department: str | None = None


class PostCreate(BaseModel):
    title: str
    content: str
    is_anonymous: bool = False
    department_tag: str | None = None


class PostOut(BaseModel):
    id: int
    title: str
    content: str
    is_anonymous: bool
    department_tag: str | None
    created_at: datetime
    author: AuthorInfo
    comment_count: int = 0

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
    created_at: datetime
    author: AuthorInfo

    model_config = {"from_attributes": True}
