from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import ChannelPost, HashtagStats

# Фиксированный список хештегов
FIXED_HASHTAGS = [
    "#Персона",
    "#Наша_азбука",
    "#Редкие_камни",
    "#Мастера_выставки",
    "#Рассказы_геологов",
    "#Новости",
    "#Наш_путеводитель",
    "#Символика_пяти_стихий"
]

async def init_hashtags(session: AsyncSession):
    """Инициализация фиксированных хештегов"""
    for tag in FIXED_HASHTAGS:
        existing = await session.execute(select(HashtagStats).where(HashtagStats.name == tag))
        if not existing.scalar_one_or_none():
            session.add(HashtagStats(name=tag))
    await session.commit()


async def get_all_hashtags(session: AsyncSession):
    """Получить все фиксированные хештеги со статистикой"""
    await init_hashtags(session)  # Убедимся, что хештеги есть в БД
    result = await session.execute(select(HashtagStats).order_by(HashtagStats.name))
    return result.scalars().all()


async def search_posts_by_hashtag(session: AsyncSession, hashtag: str):
    """Поиск постов по конкретному хештегу с медиафайлами"""
    result = await session.execute(
        select(ChannelPost)
        .where(ChannelPost.hashtags.contains(hashtag))
        .order_by(ChannelPost.date.desc())
        .options(selectinload(ChannelPost.media_files))  # Жадная загрузка медиафайлов
    )
    return result.scalars().all()


async def increment_hashtag_counter(session: AsyncSession, hashtag: str):
    """Увеличить счётчик кликов по хештегу"""
    stats = await session.execute(select(HashtagStats).where(HashtagStats.name == hashtag))
    stats = stats.scalar_one()
    stats.click_count += 1
    await session.commit()
    return stats