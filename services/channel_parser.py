import logging
from aiogram import Bot
from aiogram.types import Message, PhotoSize, Video, Document, Audio, Voice
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import ChannelPost, PostMedia, HashtagStats
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
        return []  # Реальные сообщения будут приходить через хендлер

    async def _save_messages(self, session: AsyncSession, messages: list[Message]):
        for msg in messages:
            hashtags = self._extract_hashtags(msg)
            if not hashtags:
                continue

            # Проверяем, есть ли уже такое сообщение (с await!)
            existing_post = await session.execute(
                select(ChannelPost).where(ChannelPost.message_id == msg.message_id))
            existing_post = existing_post.scalar_one_or_none()

            if existing_post:
                continue

            post = ChannelPost(
                message_id=msg.message_id,
                media_group_id=msg.media_group_id,
                text=msg.text or msg.caption,
                hashtags=",".join(hashtags)
            )

            await self._process_media(msg, post)
            session.add(post)

            for tag in hashtags:
                existing_tag = await session.execute(
                    select(HashtagStats).where(HashtagStats.name == tag))
                existing_tag = existing_tag.scalar_one_or_none()

                if not existing_tag:
                    session.add(HashtagStats(name=tag))

        await session.commit()

    async def _process_media(self, message: Message, post: ChannelPost):
        """Обрабатываем все типы медиа в сообщении"""
        order_index = 0

        # Фото - берем только самое большое (последнее в списке)
        if message.photo:
            largest_photo = message.photo[-1]  # Последний элемент - самое большое фото
            post.media_files.append(PostMedia(
                media_type="photo",
                file_id=largest_photo.file_id,
                file_unique_id=largest_photo.file_unique_id,
                file_size=largest_photo.file_size,
                width=largest_photo.width,
                height=largest_photo.height,
                order_index=order_index
            ))
            order_index += 1

        # Видео
        elif message.video:
            video = message.video
            media = PostMedia(
                media_type="video",
                file_id=video.file_id,
                file_unique_id=video.file_unique_id,
                file_size=video.file_size,
                width=video.width,
                height=video.height,
                duration=video.duration,
                thumbnail_id=video.thumbnail.file_id if video.thumbnail else None,
                order_index=order_index
            )
            post.media_files.append(media)
            order_index += 1

        # Видео
        elif message.video:
            video = message.video
            media = PostMedia(
                media_type="video",
                file_id=video.file_id,
                file_unique_id=video.file_unique_id,
                file_size=video.file_size,
                width=video.width,
                height=video.height,
                duration=video.duration,
                thumbnail_id=video.thumbnail.file_id if video.thumbnail else None,
                order_index=order_index
            )
            post.media_files.append(media)
            order_index += 1

        # Документы
        elif message.document:
            doc = message.document
            media = PostMedia(
                media_type="document",
                file_id=doc.file_id,
                file_unique_id=doc.file_unique_id,
                file_size=doc.file_size,
                mime_type=doc.mime_type,
                file_name=doc.file_name,
                thumbnail_id=doc.thumbnail.file_id if doc.thumbnail else None,
                order_index=order_index
            )
            post.media_files.append(media)
            order_index += 1

        # Аудио
        elif message.audio:
            audio = message.audio
            media = PostMedia(
                media_type="audio",
                file_id=audio.file_id,
                file_unique_id=audio.file_unique_id,
                file_size=audio.file_size,
                duration=audio.duration,
                mime_type=audio.mime_type,
                file_name=audio.file_name,
                order_index=order_index
            )
            post.media_files.append(media)
            order_index += 1

        # Голосовые сообщения
        elif message.voice:
            voice = message.voice
            media = PostMedia(
                media_type="voice",
                file_id=voice.file_id,
                file_unique_id=voice.file_unique_id,
                file_size=voice.file_size,
                duration=voice.duration,
                mime_type=voice.mime_type,
                order_index=order_index
            )
            post.media_files.append(media)
            order_index += 1

        # Можно добавить обработку других типов медиа (стикеры, анимации и т.д.)

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
        if not hashtags:
            return

        # Проверяем, есть ли уже такое сообщение (с await!)
        existing_post = await session.execute(
            select(ChannelPost).where(ChannelPost.message_id == message.message_id))
        existing_post = existing_post.scalar_one_or_none()

        if existing_post:
            return

        post = ChannelPost(
            message_id=message.message_id,
            media_group_id=message.media_group_id,
            text=message.text or message.caption,
            hashtags=",".join(hashtags)
        )

        # Обрабатываем медиафайлы
        await parser._process_media(message, post)

        session.add(post)

        # Добавляем хештеги в статистику (тоже с await!)
        for tag in hashtags:
            existing_tag = await session.execute(
                select(HashtagStats).where(HashtagStats.name == tag))
            existing_tag = existing_tag.scalar_one_or_none()

            if not existing_tag:
                session.add(HashtagStats(name=tag))

        await session.commit()