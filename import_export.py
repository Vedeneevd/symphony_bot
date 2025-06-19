import json
import re
import asyncio
from datetime import datetime
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import ChannelPost, HashtagStats
from database.session import async_session

FIXED_HASHTAGS = [
    "#новости",
    "#анонсы",
    "#истории",
    "#советы",
    "#обзоры",
    "#авторскиеукрашения",
]


async def import_from_json(file_path: str):
    """Импорт сообщений из JSON в базу данных"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        async with async_session() as session:
            # Проверяем подключение к БД
            await session.execute(select(1))
            print("✔ Соединение с БД установлено")

            # Инициализация хештегов
            await init_hashtags(session)

            added_count = 0
            for msg in data.get('messages', []):
                if not msg.get('text'):
                    continue

                # Извлекаем только нужные хештеги
                msg_hashtags = [
                    tag.lower() for tag in re.findall(r'#\w+', msg['text'])
                    if tag.lower() in [h.lower() for h in FIXED_HASHTAGS]
                ]

                if not msg_hashtags:
                    continue

                # Проверяем, есть ли уже такое сообщение
                exists = await session.execute(
                    select(ChannelPost)
                    .where(ChannelPost.message_id == msg['id'])
                )
                if not exists.scalar_one_or_none():
                    post = ChannelPost(
                        message_id=msg['id'],
                        text=msg['text'],
                        date=datetime.strptime(msg['date'], '%Y-%m-%dT%H:%M:%S'),
                        hashtags=",".join(msg_hashtags)
                    )
                    session.add(post)
                    added_count += 1

            await session.commit()
            print(f"✔ Добавлено {added_count} новых сообщений")

    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        raise


async def init_hashtags(session: AsyncSession):
    """Инициализация хештегов в базе"""
    for tag in FIXED_HASHTAGS:
        existing = await session.execute(
            select(HashtagStats).where(HashtagStats.name == tag)
        )
        if not existing.scalar_one_or_none():
            session.add(HashtagStats(name=tag))
    await session.commit()


if __name__ == "__main__":
    asyncio.run(import_from_json("result.json"))