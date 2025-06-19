import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import settings
from handlers import start, search, admin
from services.channel_parser import run_parser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def scheduled_parser():
    """Периодический запуск парсера"""
    while True:
        try:
            await run_parser()
        except Exception as e:
            logging.error(f"Ошибка парсинга: {e}")
        await asyncio.sleep(3600)  # Каждый час


async def main():
    # Инициализация aiogram бота
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()

    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(search.router)
    dp.include_router(admin.router)

    # Запуск парсера в фоне
    asyncio.create_task(scheduled_parser())

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())