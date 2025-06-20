from aiogram.utils.keyboard import InlineKeyboardBuilder

async def hashtags_keyboard(hashtags):
    builder = InlineKeyboardBuilder()
    for hashtag in hashtags:
        builder.button(
            text=f"{hashtag.name}",
            callback_data=f"hashtag:{hashtag.name}"
        )
    builder.adjust(1)  # По одному хештегу в строке
    return builder.as_markup()