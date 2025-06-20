import logging
from aiogram import Bot
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings
from database.models import ChannelPost, HashtagStats
from database.session import async_session

logger = logging.getLogger(__name__)


class ChannelParser:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def parse_new_messages(self):
        """Парсинг новых сообщений через канальные updates"""
        try:
            async with async_session() as session:
                last_id = await self._get_last_message_id(session)
                new_messages = await self._get_new_messages(last_id)

                if new_messages:
                    await self._save_messages(session, new_messages)
                    logger.info(f"Добавлено {len(new_messages)} новых сообщений")
        except Exception as e:
            logger.error(f"Ошибка парсинга: {e}")

    async def _get_last_message_id(self, session: AsyncSession) -> int:
        result = await session.execute(
            select(ChannelPost.message_id).order_by(ChannelPost.message_id.desc())
        )
        return result.scalar() or 0

    async def _get_new_messages(self, last_id: int) -> list[Message]:
        """Получаем новые сообщения через обработчик channel_post"""
        # В реальной работе сообщения будут приходить через хендлер
        return []  # Заглушка - реальные сообщения будем получать через хендлер

    async def _save_messages(self, session: AsyncSession, messages: list[Message]):
        for msg in messages:
            hashtags = self._extract_hashtags(msg)
            if hashtags:
                post = ChannelPost(
                    message_id=msg.message_id,
                    text=msg.text or msg.caption,
                    hashtags=",".join(hashtags)
                )
                session.add(post)

                for tag in hashtags:
                    if not await session.execute(
                            select(HashtagStats).where(HashtagStats.name == tag)
                    ).scalar_one_or_none():
                        session.add(HashtagStats(name=tag))

        await session.commit()

    def _extract_hashtags(self, message: Message) -> list[str]:
        text = message.text or message.caption or ""
        entities = message.entities or message.caption_entities or []
        return [
            text[e.offset:e.offset + e.length]
            for e in entities if e.type == "hashtag"
        ]


async def process_message(message: Message, bot: Bot):
    """Обработчик новых сообщений из канала"""
    parser = ChannelParser(bot)
    async with async_session() as session:
        hashtags = parser._extract_hashtags(message)
        if hashtags:
            post = ChannelPost(
                message_id=message.message_id,
                text=message.text or message.caption,
                hashtags=",".join(hashtags)
            )
            session.add(post)
            await session.commit()