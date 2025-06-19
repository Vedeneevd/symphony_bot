import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import settings
from handlers import start, search, admin
from handlers.channel import router as channel_router
from services.channel_parser import ChannelParser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def scheduled_parser(bot: Bot):
    while True:
        try:
            parser = ChannelParser(bot)
            await parser.parse_new_messages()
        except Exception as e:
            logging.error(f"Parser error: {e}")
        await asyncio.sleep(5)


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
    dp.include_router(channel_router)

    # Запуск парсера в фоне
    asyncio.create_task(scheduled_parser(bot))

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())