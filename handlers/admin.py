from aiogram import Router, types, F
from aiogram.filters import Command
from database.crud import get_all_hashtags
from database.session import async_session

router = Router()


@router.message(Command("stats"))
@router.callback_query(F.data.startswith("stats"))
async def show_stats(message: types.Message | types.CallbackQuery):
    async with async_session() as session:
        hashtags = await get_all_hashtags(session)
        stats_text = "📊 Статистика просмотров рубрик:\n\n"
        for hashtag in sorted(hashtags, key=lambda x: x.click_count, reverse=True):
            stats_text += f"{hashtag.name}: {hashtag.click_count} просмотров\n"

    if isinstance(message, types.CallbackQuery):
        await message.message.edit_text(stats_text)
    else:
        await message.answer(stats_text)