"""add schools and boards

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-27

"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_SCHOOL_SLUG = "zhijiang-university"
RANK_SOURCE = "THE World University Rankings 2026 Japan table, snapshot 2026-06-27"

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

SCHOOLS = [
    ("the-university-of-tokyo", "The University of Tokyo", "东京大学", "東京大学", "1", ["University of Tokyo", "东京大学", "東京大学", "东大", "東大", "Todai"]),
    ("kyoto-university", "Kyoto University", "京都大学", "京都大学", "2", ["Kyoto University", "京都大学", "京大", "Kyodai"]),
    ("tohoku-university", "Tohoku University", "东北大学", "東北大学", "3", ["Tohoku University", "东北大学", "東北大学"]),
    ("the-university-of-osaka", "The University of Osaka", "大阪大学", "大阪大学", "4", ["Osaka University", "The University of Osaka", "大阪大学", "阪大"]),
    ("institute-of-science-tokyo", "Institute of Science Tokyo", "东京科学大学", "東京科学大学", "5", ["Institute of Science Tokyo", "Science Tokyo", "东京科学大学", "東京科学大学", "東工大", "Tokyo Tech"]),
    ("nagoya-university", "Nagoya University", "名古屋大学", "名古屋大学", "6", ["Nagoya University", "名古屋大学", "名大"]),
    ("kyushu-university", "Kyushu University", "九州大学", "九州大学", "7", ["Kyushu University", "九州大学", "九大"]),
    ("hokkaido-university", "Hokkaido University", "北海道大学", "北海道大学", "=8", ["Hokkaido University", "北海道大学", "北大"]),
    ("university-of-tsukuba", "University of Tsukuba", "筑波大学", "筑波大学", "=8", ["University of Tsukuba", "筑波大学"]),
    ("juntendo-university", "Juntendo University", "顺天堂大学", "順天堂大学", "10", ["Juntendo University", "顺天堂大学", "順天堂大学"]),
    ("hiroshima-university", "Hiroshima University", "广岛大学", "広島大学", "=11", ["Hiroshima University", "广岛大学", "広島大学"]),
    ("keio-university", "Keio University", "庆应义塾大学", "慶應義塾大学", "=11", ["Keio University", "庆应义塾大学", "慶應義塾大学", "慶應", "Keio"]),
    ("kobe-university", "Kobe University", "神户大学", "神戸大学", "=11", ["Kobe University", "神户大学", "神戸大学"]),
    ("the-university-of-aizu", "The University of Aizu", "会津大学", "会津大学", "=11", ["The University of Aizu", "University of Aizu", "会津大学"]),
    ("wakayama-medical-university", "Wakayama Medical University", "和歌山县立医科大学", "和歌山県立医科大学", "=15", ["Wakayama Medical University", "和歌山県立医科大学", "和歌山县立医科大学"]),
    ("waseda-university", "Waseda University", "早稻田大学", "早稲田大学", "=15", ["Waseda University", "早稻田大学", "早稲田大学", "早大"]),
    ("chiba-university", "Chiba University", "千叶大学", "千葉大学", "=17", ["Chiba University", "千叶大学", "千葉大学"]),
    ("fujita-health-university", "Fujita Health University", "藤田医科大学", "藤田医科大学", "=17", ["Fujita Health University", "藤田医科大学"]),
    ("hamamatsu-university-school-of-medicine", "Hamamatsu University School of Medicine", "浜松医科大学", "浜松医科大学", "=17", ["Hamamatsu University School of Medicine", "浜松医科大学"]),
    ("kanazawa-university", "Kanazawa University", "金泽大学", "金沢大学", "=17", ["Kanazawa University", "金泽大学", "金沢大学"]),
    ("kumamoto-university", "Kumamoto University", "熊本大学", "熊本大学", "=17", ["Kumamoto University", "熊本大学"]),
    ("kyoto-prefectural-university-of-medicine", "Kyoto Prefectural University of Medicine", "京都府立医科大学", "京都府立医科大学", "=17", ["Kyoto Prefectural University of Medicine", "京都府立医科大学"]),
    ("nippon-medical-school", "Nippon Medical School", "日本医科大学", "日本医科大学", "=17", ["Nippon Medical School", "日本医科大学"]),
    ("okayama-university", "Okayama University", "冈山大学", "岡山大学", "=17", ["Okayama University", "冈山大学", "岡山大学"]),
    ("tokyo-medical-university", "Tokyo Medical University", "东京医科大学", "東京医科大学", "=17", ["Tokyo Medical University", "东京医科大学", "東京医科大学"]),
    ("yokohama-city-university", "Yokohama City University", "横滨市立大学", "横浜市立大学", "=17", ["Yokohama City University", "横滨市立大学", "横浜市立大学"]),
    ("aichi-medical-university", "Aichi Medical University", "爱知医科大学", "愛知医科大学", "=27", ["Aichi Medical University", "爱知医科大学", "愛知医科大学"]),
    ("gifu-university", "Gifu University", "岐阜大学", "岐阜大学", "=27", ["Gifu University", "岐阜大学"]),
    ("hitotsubashi-university", "Hitotsubashi University", "一桥大学", "一橋大学", "=27", ["Hitotsubashi University", "一桥大学", "一橋大学"]),
    ("hosei-university", "Hosei University", "法政大学", "法政大学", "=27", ["Hosei University", "法政大学"]),
    ("hyogo-medical-university", "Hyogo Medical University", "兵库医科大学", "兵庫医科大学", "=27", ["Hyogo Medical University", "兵库医科大学", "兵庫医科大学"]),
    ("kansai-medical-university", "Kansai Medical University", "关西医科大学", "関西医科大学", "=27", ["Kansai Medical University", "关西医科大学", "関西医科大学"]),
    ("kindai-university", "Kindai University", "近畿大学", "近畿大学", "=27", ["Kindai University", "近畿大学", "近大"]),
    ("kurume-university", "Kurume University", "久留米大学", "久留米大学", "=27", ["Kurume University", "久留米大学"]),
    ("kyushu-institute-of-technology", "Kyushu Institute of Technology (Kyutech)", "九州工业大学", "九州工業大学", "=27", ["Kyushu Institute of Technology", "Kyutech", "九州工业大学", "九州工業大学"]),
    ("nagasaki-university", "Nagasaki University", "长崎大学", "長崎大学", "=27", ["Nagasaki University", "长崎大学", "長崎大学"]),
    ("nagoya-city-university", "Nagoya City University", "名古屋市立大学", "名古屋市立大学", "=27", ["Nagoya City University", "名古屋市立大学"]),
    ("niigata-university", "Niigata University", "新潟大学", "新潟大学", "=27", ["Niigata University", "新潟大学"]),
    ("osaka-metropolitan-university", "Osaka Metropolitan University", "大阪公立大学", "大阪公立大学", "=27", ["Osaka Metropolitan University", "大阪公立大学"]),
    ("sapporo-medical-university", "Sapporo Medical University", "札幌医科大学", "札幌医科大学", "=27", ["Sapporo Medical University", "札幌医科大学"]),
    ("shiga-university-of-medical-science", "Shiga University of Medical Science", "滋贺医科大学", "滋賀医科大学", "=27", ["Shiga University of Medical Science", "滋贺医科大学", "滋賀医科大学"]),
    ("shinshu-university", "Shinshu University", "信州大学", "信州大学", "=27", ["Shinshu University", "信州大学"]),
    ("the-jikei-university-school-of-medicine", "The Jikei University School of Medicine", "东京慈惠会医科大学", "東京慈恵会医科大学", "=27", ["The Jikei University School of Medicine", "Jikei University", "东京慈惠会医科大学", "東京慈恵会医科大学", "慈恵医大"]),
    ("the-university-of-electro-communications", "The University of Electro-Communications", "电气通信大学", "電気通信大学", "=27", ["The University of Electro-Communications", "University of Electro-Communications", "电气通信大学", "電気通信大学", "電通大"]),
    ("tokai-university", "Tokai University", "东海大学", "東海大学", "=27", ["Tokai University", "东海大学", "東海大学"]),
    ("tokushima-university", "Tokushima University", "德岛大学", "徳島大学", "=27", ["Tokushima University", "德岛大学", "徳島大学"]),
    ("tokyo-university-of-agriculture-and-technology", "Tokyo University of Agriculture and Technology", "东京农工大学", "東京農工大学", "=27", ["Tokyo University of Agriculture and Technology", "东京农工大学", "東京農工大学", "農工大"]),
    ("tokyo-university-of-science", "Tokyo University of Science", "东京理科大学", "東京理科大学", "=27", ["Tokyo University of Science", "东京理科大学", "東京理科大学", "理科大"]),
    ("toyohashi-university-of-technology", "Toyohashi University of Technology (TUT)", "丰桥技术科学大学", "豊橋技術科学大学", "=27", ["Toyohashi University of Technology", "TUT", "丰桥技术科学大学", "豊橋技術科学大学"]),
    ("university-of-occupational-and-environmental-health-japan", "University of Occupational and Environmental Health, Japan", "产业医科大学", "産業医科大学", "=27", ["University of Occupational and Environmental Health", "产业医科大学", "産業医科大学"]),
]


def normalize(value: str) -> str:
    return re.sub(r"[\s・･·,，.。()（）\\-_'\"/]+", "", value).casefold()


def add_alias(conn, alias_table, school_id: int, alias: str, locale: str | None = None) -> None:
    normalized = normalize(alias)
    exists = conn.execute(sa.select(alias_table.c.id).where(alias_table.c.alias_normalized == normalized)).first()
    if not exists:
        conn.execute(alias_table.insert().values(school_id=school_id, alias=alias, alias_normalized=normalized, locale=locale))


def upgrade() -> None:
    now = datetime.utcnow()

    op.create_table(
        "schools",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("slug", sa.String(length=120), nullable=False, unique=True),
        sa.Column("name_zh", sa.String(length=200), nullable=False),
        sa.Column("name_en", sa.String(length=200), nullable=False),
        sa.Column("name_ja", sa.String(length=200), nullable=False),
        sa.Column("country", sa.String(length=50), nullable=False, server_default="Japan"),
        sa.Column("kind", sa.String(length=30), nullable=False, server_default="real"),
        sa.Column("rank_source", sa.String(length=120), nullable=True),
        sa.Column("rank_label", sa.String(length=30), nullable=True),
        sa.Column("rank_order", sa.Integer(), nullable=True),
        sa.Column("theme", sa.String(length=40), nullable=False, server_default="standard"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "school_aliases",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("alias", sa.String(length=200), nullable=False),
        sa.Column("alias_normalized", sa.String(length=200), nullable=False, unique=True),
        sa.Column("locale", sa.String(length=20), nullable=True),
    )
    op.create_table(
        "boards",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("boards.id"), nullable=True),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("school_id", "parent_id", "slug", name="uq_board_school_parent_slug"),
    )

    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("school_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("school_name_custom", sa.String(length=200), nullable=True))
        batch_op.create_foreign_key("fk_users_school_id_schools", "schools", ["school_id"], ["id"])
    with op.batch_alter_table("posts") as batch_op:
        batch_op.add_column(sa.Column("school_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("board_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_posts_school_id_schools", "schools", ["school_id"], ["id"])
        batch_op.create_foreign_key("fk_posts_board_id_boards", "boards", ["board_id"], ["id"])

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
    posts = sa.table(
        "posts",
        sa.column("author_id", sa.Integer),
        sa.column("title", sa.String),
        sa.column("content", sa.Text),
        sa.column("is_anonymous", sa.Boolean),
        sa.column("department_tag", sa.String),
        sa.column("category", sa.String),
        sa.column("visibility", sa.String),
        sa.column("is_pinned", sa.Boolean),
        sa.column("is_deleted", sa.Boolean),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
        sa.column("school_id", sa.Integer),
        sa.column("board_id", sa.Integer),
    )

    conn.execute(
        schools.insert().values(
            slug=DEFAULT_SCHOOL_SLUG,
            name_zh="枝江大学",
            name_en="Zhijiang University",
            name_ja="枝江大学",
            country="Public",
            kind="virtual_public",
            rank_source=None,
            rank_label=None,
            rank_order=None,
            theme="zhijiang",
            is_active=True,
            created_at=now,
        )
    )
    zhijiang_id = conn.execute(sa.select(schools.c.id).where(schools.c.slug == DEFAULT_SCHOOL_SLUG)).scalar_one()
    for alias in ["枝江大学", "枝江", "公共区", "公共板块", "Zhijiang University", "Zhijiang"]:
        add_alias(conn, aliases, zhijiang_id, alias)

    for order, (slug, name_en, name_zh, name_ja, rank_label, alias_values) in enumerate(SCHOOLS, start=1):
        conn.execute(
            schools.insert().values(
                slug=slug,
                name_zh=name_zh,
                name_en=name_en,
                name_ja=name_ja,
                country="Japan",
                kind="real",
                rank_source=RANK_SOURCE,
                rank_label=rank_label,
                rank_order=order,
                theme="standard",
                is_active=True,
                created_at=now,
            )
        )
        school_id = conn.execute(sa.select(schools.c.id).where(schools.c.slug == slug)).scalar_one()
        for alias in {name_en, name_zh, name_ja, *alias_values}:
            add_alias(conn, aliases, school_id, alias)

    school_rows = conn.execute(sa.select(schools.c.id, schools.c.slug, schools.c.name_zh, schools.c.kind)).all()
    board_ids: dict[tuple[int, str], int] = {}
    for school_id, slug, name_zh, kind in school_rows:
        defaults = PUBLIC_SCHOOL_BOARDS if slug == DEFAULT_SCHOOL_SLUG else REAL_SCHOOL_BOARDS
        for board_slug, board_name, description, sort_order in defaults:
            conn.execute(
                boards.insert().values(
                    school_id=school_id,
                    parent_id=None,
                    slug=board_slug,
                    name=board_name,
                    description=description,
                    status="approved",
                    sort_order=sort_order,
                    created_by=None,
                    created_at=now,
                    updated_at=now,
                )
            )
            board_id = conn.execute(
                sa.select(boards.c.id).where(
                    boards.c.school_id == school_id,
                    boards.c.parent_id.is_(None),
                    boards.c.slug == board_slug,
                )
            ).scalar_one()
            board_ids[(school_id, board_slug)] = board_id
        notice_id = board_ids[(school_id, "notice")]
        if slug == DEFAULT_SCHOOL_SLUG:
            title = "枝江大学公共区简介"
            content = "枝江大学是 UTOO 的虚拟公共区，不是真实学校。未填写学校的用户会默认显示为枝江大学，跨学校公共讨论也会进入这里。"
        else:
            title = f"{name_zh} 简介"
            content = f"{name_zh} 板块用于收集该校相关的课程、研究室、生活、租房和就职讨论。学校种子来自 {RANK_SOURCE}。"
        conn.execute(
            posts.insert().values(
                author_id=None,
                title=title,
                content=content,
                is_anonymous=False,
                department_tag=None,
                category="公告",
                visibility="normal",
                is_pinned=True,
                is_deleted=False,
                created_at=now,
                updated_at=now,
                school_id=school_id,
                board_id=notice_id,
            )
        )

    conn.execute(sa.text("UPDATE users SET school_id = :school_id WHERE school_id IS NULL"), {"school_id": zhijiang_id})
    category_to_slug = {
        "公告": "notice",
        "课程": "general",
        "研究室": "general",
        "生活": "life",
        "租房": "housing",
        "就职": "career",
        "闲聊": "chat",
    }
    conn.execute(sa.text("UPDATE posts SET school_id = :school_id WHERE school_id IS NULL"), {"school_id": zhijiang_id})
    for category, board_slug in category_to_slug.items():
        board_id = board_ids[(zhijiang_id, board_slug)]
        conn.execute(
            sa.text("UPDATE posts SET board_id = :board_id WHERE board_id IS NULL AND category = :category"),
            {"board_id": board_id, "category": category},
        )
    conn.execute(sa.text("UPDATE posts SET board_id = :board_id WHERE board_id IS NULL"), {"board_id": board_ids[(zhijiang_id, "general")]})


def downgrade() -> None:
    with op.batch_alter_table("posts") as batch_op:
        batch_op.drop_constraint("fk_posts_board_id_boards", type_="foreignkey")
        batch_op.drop_constraint("fk_posts_school_id_schools", type_="foreignkey")
        batch_op.drop_column("board_id")
        batch_op.drop_column("school_id")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("fk_users_school_id_schools", type_="foreignkey")
        batch_op.drop_column("school_name_custom")
        batch_op.drop_column("school_id")
    op.drop_table("boards")
    op.drop_table("school_aliases")
    op.drop_table("schools")
