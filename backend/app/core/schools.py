import hashlib
import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.school import Board, School, SchoolAlias

DEFAULT_SCHOOL_SLUG = "zhijiang-university"
SCHOOL_KIND_REAL = "real"
SCHOOL_KIND_PUBLIC = "virtual_public"
BOARD_STATUS_APPROVED = "approved"
BOARD_STATUS_PENDING = "pending"
BOARD_STATUS_REJECTED = "rejected"
BOARD_STATUS_HIDDEN = "hidden"

REAL_SCHOOL_BOARDS = [
    ("notice", "公告", "学校公告、规则和简介", 10),
    ("course", "课程", "选课、授课、作业和考试经验", 20),
    ("lab", "研究室", "实验室、导师、申请和研究生活", 30),
    ("life", "生活", "手续、校园服务和日常经验", 40),
    ("housing", "租房", "区域、预算、通勤和搬家信息", 50),
    ("career", "就职", "实习、求职、面试和行业讨论", 60),
    ("chat", "闲聊", "轻量交流和社区互助", 70),
]

PUBLIC_SCHOOL_BOARDS = [
    ("notice", "公告", "公共区公告、规则和简介", 10),
    ("general", "综合讨论", "跨学校讨论和公共话题", 20),
    ("life", "生活", "在日生活、手续和日常经验", 30),
    ("housing", "租房", "租房、搬家、通勤和区域信息", 40),
    ("career", "就职", "实习、求职、面试和行业讨论", 50),
    ("chat", "闲聊", "轻量交流和社区互助", 60),
    ("help", "提问求助", "新手问题、求助和信息确认", 70),
]

CATEGORY_BOARD_SLUG = {
    "公告": "notice",
    "课程": "course",
    "研究室": "lab",
    "生活": "life",
    "租房": "housing",
    "就职": "career",
    "闲聊": "chat",
}

PUBLIC_CATEGORY_BOARD_SLUG = {
    "公告": "notice",
    "课程": "general",
    "研究室": "general",
    "生活": "life",
    "租房": "housing",
    "就职": "career",
    "闲聊": "chat",
}


def normalize_school_alias(value: str) -> str:
    return re.sub(r"[\s・･·,，.。()（）\\-_'\"/]+", "", value).casefold()


def slugify(value: str, fallback_prefix: str = "item") -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if normalized:
        return normalized[:100]
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]
    return f"{fallback_prefix}-{digest}"


async def get_default_school(db: AsyncSession) -> School:
    result = await db.execute(select(School).where(School.slug == DEFAULT_SCHOOL_SLUG))
    school = result.scalar_one_or_none()
    if not school:
        raise RuntimeError("Default public school seed is missing")
    return school


async def resolve_school_input(db: AsyncSession, school_input: str | None) -> tuple[School, str | None]:
    default_school = await get_default_school(db)
    value = (school_input or "").strip()
    if not value:
        return default_school, None
    normalized = normalize_school_alias(value)
    alias_result = await db.execute(select(SchoolAlias).where(SchoolAlias.alias_normalized == normalized))
    alias = alias_result.scalar_one_or_none()
    if alias:
        school_result = await db.execute(select(School).where(School.id == alias.school_id, School.is_active == True))  # noqa: E712
        school = school_result.scalar_one_or_none()
        if school:
            return school, None
    return default_school, value


async def default_board_for_category(db: AsyncSession, school_id: int, category: str | None) -> Board:
    school_result = await db.execute(select(School).where(School.id == school_id))
    school = school_result.scalar_one_or_none()
    if not school:
        school = await get_default_school(db)
    mapping = PUBLIC_CATEGORY_BOARD_SLUG if school.slug == DEFAULT_SCHOOL_SLUG else CATEGORY_BOARD_SLUG
    slug = mapping.get(category or "闲聊", "chat")
    result = await db.execute(
        select(Board).where(
            Board.school_id == school.id,
            Board.parent_id.is_(None),
            Board.slug == slug,
            Board.status == BOARD_STATUS_APPROVED,
        )
    )
    board = result.scalar_one_or_none()
    if not board:
        fallback = await db.execute(
            select(Board).where(
                Board.school_id == school.id,
                Board.parent_id.is_(None),
                Board.status == BOARD_STATUS_APPROVED,
            ).order_by(Board.sort_order.asc())
        )
        board = fallback.scalars().first()
    if not board:
        raise RuntimeError("Default board seed is missing")
    return board
