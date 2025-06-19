from aiogram import Router, types
from aiogram.filters import Command
from database.crud import get_all_hashtags
from database.session import async_session
from keyboards.inline import hashtags_keyboard

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    async with async_session() as session:
        hashtags = await get_all_hashtags(session)
        keyboard = await hashtags_keyboard(hashtags)
        await message.answer(
            "Выберите рубрику для поиска:",
            reply_markup=keyboard
        )