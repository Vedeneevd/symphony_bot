import logging
from telethon import TelegramClient
from telethon.tl.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings
from database.models import ChannelPost, HashtagStats
from database.session import async_session

logger = logging.getLogger(__name__)


class ChannelParser:
    def __init__(self):
        self.client = TelegramClient(
            'channel_parser',
            settings.TELEGRAM_API_ID,
            settings.TELEGRAM_API_HASH
        )

    async def parse_new_messages(self):
        """Основной метод парсинга сообщений"""
        async with self.client:
            try:
                async with async_session() as session:
                    last_id = await self._get_last_message_id(session)
                    messages = await self._fetch_messages(last_id)

                    if messages:
                        await self._save_messages(session, messages)
                        logger.info(f"Добавлено {len(messages)} новых сообщений")
            except Exception as e:
                logger.error(f"Ошибка парсинга: {e}")
                raise

    async def _get_last_message_id(self, session: AsyncSession) -> int:
        result = await session.execute(
            select(ChannelPost.message_id).order_by(ChannelPost.message_id.desc())
        )
        return result.scalar() or 0

    async def _fetch_messages(self, last_id: int) -> list[Message]:
        messages = []
        async for message in self.client.iter_messages(
                settings.CHANNEL_ID,
                limit=100,
                min_id=last_id,
                reverse=True
        ):
            if message.text or message.caption:
                messages.append(message)
        return messages

    async def _save_messages(self, session: AsyncSession, messages: list[Message]):
        new_posts = []
        for message in messages:
            hashtags = self._extract_hashtags(message)
            if hashtags:
                new_posts.append(ChannelPost(
                    message_id=message.id,
                    text=message.text or message.caption,
                    hashtags=",".join(hashtags)
                ))

                for tag in hashtags:
                    if not await session.execute(
                            select(HashtagStats).where(HashtagStats.name == tag)
                    ).scalar_one_or_none():
                        session.add(HashtagStats(name=tag))

        if new_posts:
            session.add_all(new_posts)
            await session.commit()

    def _extract_hashtags(self, message: Message) -> list[str]:
        text = message.text or message.caption or ""
        entities = message.entities or message.caption_entities or []

        return list({
            text[entity.offset:entity.offset + entity.length].lower()
            for entity in entities
            if getattr(entity, 'type', None) == 'hashtag'
        })


async def run_parser():
    parser = ChannelParser()
    await parser.parse_new_messages()