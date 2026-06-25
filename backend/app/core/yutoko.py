import random
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.agent_keys import agent_key_prefix, generate_agent_api_key
from app.core.moderation import VISIBILITY_NORMAL
from app.core.security import hash_password
from app.models.agent import Agent
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User

YUTOKO_AGENT_NAME = "Yutoko"
YUTOKO_AGENT_DESCRIPTION = "UTOO mascot agent for gentle post greetings"
YUTOKO_COMMENT_PROBABILITY = 0.35

YUTOKO_LINES = {
    "课程": [
        "这门课的信息我先放个银杏书签，后来的同学也许会很需要这条线索。",
        "课程帖收到。欢迎补充作业量、考试形式和推荐预习材料。"
    ],
    "研究室": [
        "研究室情报很珍贵，欢迎把氛围、方向和联系经验慢慢补全。",
        "我把这篇别上银杏叶了。后来选 lab 的同学可能会感谢你。"
    ],
    "生活": [
        "生活经验也很重要。愿这条帖子帮大家少踩一点坑。",
        "校园生活记录中。小事也可能是别人刚好需要的答案。"
    ],
    "租房": [
        "租房信息请注意隐私和时效，也欢迎补充车站、通勤和费用范围。",
        "这类帖子很实用，我在旁边帮你看着讨论秩序。"
    ],
    "就职": [
        "就职经验已收到。欢迎补充时间线、准备材料和面试感受。",
        "这条可能会帮到未来投递的人，先给它挂一片银杏叶。"
    ],
    "闲聊": [
        "新帖出现。Yutoko 在角落值班，祝这串讨论顺利展开。",
        "我探头看到了新话题。轻松聊，但也记得对彼此温柔一点。"
    ],
}


async def get_or_create_yutoko_agent(db: AsyncSession) -> Agent | None:
    result = await db.execute(select(Agent).where(Agent.name == YUTOKO_AGENT_NAME))
    agent = result.scalar_one_or_none()
    if agent:
        return agent if agent.is_active else None

    owner_result = await db.execute(
        select(User).order_by(User.is_admin.desc(), User.id.asc()).limit(1)
    )
    owner = owner_result.scalar_one_or_none()
    if not owner:
        return None

    api_key = generate_agent_api_key()
    agent = Agent(
        name=YUTOKO_AGENT_NAME,
        description=YUTOKO_AGENT_DESCRIPTION,
        api_key_prefix=agent_key_prefix(api_key),
        api_key_hash=hash_password(api_key),
        created_by=owner.id,
    )
    db.add(agent)
    await db.flush()
    return agent


async def maybe_create_yutoko_comment(db: AsyncSession, post: Post) -> Comment | None:
    if post.visibility != VISIBILITY_NORMAL or post.is_deleted or post.category == "公告":
        return None

    agent = await get_or_create_yutoko_agent(db)
    if not agent:
        return None

    existing = await db.execute(
        select(Comment).where(Comment.post_id == post.id, Comment.agent_id == agent.id).limit(1)
    )
    if existing.scalar_one_or_none():
        return None

    if random.random() > YUTOKO_COMMENT_PROBABILITY:
        return None

    lines = YUTOKO_LINES.get(post.category, YUTOKO_LINES["闲聊"])
    comment = Comment(
        post_id=post.id,
        agent_id=agent.id,
        author_id=None,
        content=random.choice(lines),
        is_anonymous=False,
    )
    agent.last_posted_at = datetime.now(timezone.utc)
    db.add(comment)
    await db.flush()
    return comment
