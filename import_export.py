import json
import re
from datetime import datetime
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import ChannelPost, HashtagStats
from database.session import async_session

FIXED_HASHTAGS = [
    "#новости",
    "#анонсы",
    "#истории",
    "#советы",
    "#обзоры",
    "#ювелирныйсет",
]


def extract_text_and_hashtags(msg: dict) -> tuple[str, list[str]]:
    """Извлекает текст и хештеги из сообщения любого формата"""
    text = ""
    hashtags = []

    # Обработка разных форматов сообщений
    if isinstance(msg.get('text'), str):
        text = msg['text']
    elif isinstance(msg.get('text'), list):
        # Для сообщений с несколькими частями (текст + медиа)
        text_parts = []
        for item in msg['text']:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict) and 'text' in item:
                text_parts.append(item['text'])
        text = ' '.join(text_parts)

    # Извлекаем хештеги только если есть текст
    if text:
        hashtags = [
            tag.lower() for tag in re.findall(r'#\w+', text)
            if tag.lower() in [h.lower() for h in FIXED_HASHTAGS]
        ]

    return text, hashtags


async def import_from_json(file_path: str):
    """Импорт сообщений из JSON с обработкой всех форматов"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"Всего сообщений в экспорте: {len(data.get('messages', []))}")

        async with async_session() as session:
            # Проверка подключения
            await session.execute(select(1))
            print("✔ Соединение с БД установлено")

            # Инициализация хештегов
            await init_hashtags(session)

            added_count = 0
            for msg in data.get('messages', []):
                try:
                    text, msg_hashtags = extract_text_and_hashtags(msg)
                    if not text or not msg_hashtags:
                        continue

                    # Проверка на дубликаты
                    exists = await session.execute(
                        select(ChannelPost)
                        .where(ChannelPost.message_id == msg['id'])
                    )
                    if exists.scalar_one_or_none():
                        continue

                    # Добавление сообщения
                    post = ChannelPost(
                        message_id=msg['id'],
                        text=text,
                        date=datetime.strptime(msg['date'], '%Y-%m-%dT%H:%M:%S'),
                        hashtags=",".join(msg_hashtags)
                    )
                    session.add(post)
                    added_count += 1

                except Exception as e:
                    print(f"Ошибка в сообщении ID {msg.get('id')}: {str(e)}")
                    continue

            await session.commit()
            print(f"✔ Успешно добавлено {added_count} сообщений")

    except Exception as e:
        print(f"❌ Критическая ошибка импорта: {str(e)}")
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
    import asyncio

    asyncio.run(import_from_json("result.json"))