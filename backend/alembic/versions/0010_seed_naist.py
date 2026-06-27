"""seed naist school

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-27

"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NAIST_SLUG = "nara-institute-of-science-and-technology"

REAL_SCHOOL_BOARDS = [
    ("notice", "公告", "学校公告、规则和简介", 10),
    ("course", "课程", "选课、授课、作业和考试经验", 20),
    ("lab", "研究室", "实验室、导师、申请和研究生活", 30),
    ("life", "生活", "手续、校园服务和日常经验", 40),
    ("housing", "租房", "区域、预算、通勤和搬家信息", 50),
    ("career", "就职", "实习、求职、面试和行业讨论", 60),
    ("chat", "闲聊", "轻量交流和社区互助", 70),
]


def normalize(value: str) -> str:
    return re.sub(r"[\s・･·,，.。()（）\\-_'\"/]+", "", value).casefold()


def add_alias(conn, aliases, school_id: int, alias: str, locale: str | None = None) -> None:
    normalized = normalize(alias)
    exists = conn.execute(sa.select(aliases.c.id).where(aliases.c.alias_normalized == normalized)).first()
    if not exists:
        conn.execute(aliases.insert().values(school_id=school_id, alias=alias, alias_normalized=normalized, locale=locale))


def upgrade() -> None:
    now = datetime.utcnow()
    conn = op.get_bind()
    schools = sa.table(
        "schools",
        sa.column("id", sa.Integer),
        sa.column("slug", sa.String),
        sa.column("name_zh", sa.String),
        sa.column("name_en", sa.String),
        sa.column("name_ja", sa.String),
        sa.column("country", sa.String),
        sa.column("kind", sa.String),
        sa.column("rank_source", sa.String),
        sa.column("rank_label", sa.String),
        sa.column("rank_order", sa.Integer),
        sa.column("theme", sa.String),
        sa.column("is_active", sa.Boolean),
        sa.column("created_at", sa.DateTime),
    )
    aliases = sa.table(
        "school_aliases",
        sa.column("id", sa.Integer),
        sa.column("school_id", sa.Integer),
        sa.column("alias", sa.String),
        sa.column("alias_normalized", sa.String),
        sa.column("locale", sa.String),
    )
    boards = sa.table(
        "boards",
        sa.column("id", sa.Integer),
        sa.column("school_id", sa.Integer),
        sa.column("parent_id", sa.Integer),
        sa.column("slug", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("status", sa.String),
        sa.column("sort_order", sa.Integer),
        sa.column("created_by", sa.Integer),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )

    school_row = conn.execute(sa.select(schools.c.id).where(schools.c.slug == NAIST_SLUG)).first()
    if school_row:
        school_id = school_row[0]
    else:
        conn.execute(
            schools.insert().values(
                slug=NAIST_SLUG,
                name_zh="奈良先端科学技术大学院大学",
                name_en="Nara Institute of Science and Technology",
                name_ja="奈良先端科学技術大学院大学",
                country="Japan",
                kind="real",
                rank_source=None,
                rank_label=None,
                rank_order=None,
                theme="standard",
                is_active=True,
                created_at=now,
            )
        )
        school_id = conn.execute(sa.select(schools.c.id).where(schools.c.slug == NAIST_SLUG)).scalar_one()

    for alias, locale in [
        ("奈良先端科学技术大学院大学", "zh"),
        ("Nara Institute of Science and Technology", "en"),
        ("奈良先端科学技術大学院大学", "ja"),
        ("NAIST", None),
        ("naist", None),
        ("奈良先端", None),
        ("奈良先端大", None),
    ]:
        add_alias(conn, aliases, school_id, alias, locale)

    for slug, name, description, sort_order in REAL_SCHOOL_BOARDS:
        exists = conn.execute(
            sa.select(boards.c.id).where(
                boards.c.school_id == school_id,
                boards.c.parent_id.is_(None),
                boards.c.slug == slug,
            )
        ).first()
        if not exists:
            conn.execute(
                boards.insert().values(
                    school_id=school_id,
                    parent_id=None,
                    slug=slug,
                    name=name,
                    description=description,
                    status="approved",
                    sort_order=sort_order,
                    created_by=None,
                    created_at=now,
                    updated_at=now,
                )
            )


def downgrade() -> None:
    # Keep user/content references stable; this seed migration is intentionally not destructive.
    pass
