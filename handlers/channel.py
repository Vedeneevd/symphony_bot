from aiogram import Router, F
from aiogram.types import Message
from services.channel_parser import process_message

router = Router()

@router.channel_post(F.text | F.caption)
async def handle_channel_post(message: Message, bot):
    """Обрабатывает новые посты в канале"""
    await process_message(message, bot)