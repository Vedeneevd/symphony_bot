from aiogram import Router, types, F, Bot
from aiogram.types import InputMediaPhoto, InputMediaVideo
from database.crud import search_posts_by_hashtag, increment_hashtag_counter
from database.session import async_session
from sqlalchemy.orm import selectinload

router = Router()


@router.callback_query(F.data.startswith("hashtag:"))
async def show_hashtag_posts(callback: types.CallbackQuery, bot: Bot):
    hashtag = callback.data.split(":")[1]

    async with async_session() as session:
        # Увеличиваем счётчик
        await increment_hashtag_counter(session, hashtag)

        # Ищем посты с загрузкой связанных медиафайлов
        posts = await search_posts_by_hashtag(session, hashtag)

        if not posts:
            await callback.message.answer(f"По рубрике {hashtag} пока нет публикаций.")
            await callback.answer()
            return

        # Ограничиваем вывод (например, 5 последних постов)
        for post in posts:
            if not post.media_files:
                # Если нет медиа - просто отправляем текст
                await callback.message.answer(post.text or "📄 Сообщение без текста")
                continue

            # Группируем медиа по типам для правильной отправки
            media_group = []
            for media in sorted(post.media_files, key=lambda x: x.order_index):
                if media.media_type == 'photo':
                    media_group.append(InputMediaPhoto(
                        media=media.file_id,
                        caption=post.text if not media_group else None
                    ))
                elif media.media_type == 'video':
                    media_group.append(InputMediaVideo(
                        media=media.file_id,
                        caption=post.text if not media_group else None
                    ))
                # Можно добавить обработку других типов медиа

            try:
                if len(media_group) > 1:
                    # Если медиа несколько - отправляем как альбом
                    await bot.send_media_group(
                        chat_id=callback.message.chat.id,
                        media=media_group
                    )
                else:
                    # Если одно медиа - отправляем соответствующе
                    media = media_group[0]
                    if isinstance(media, InputMediaPhoto):
                        await bot.send_photo(
                            chat_id=callback.message.chat.id,
                            photo=media.media,
                            caption=media.caption
                        )
                    elif isinstance(media, InputMediaVideo):
                        await bot.send_video(
                            chat_id=callback.message.chat.id,
                            video=media.media,
                            caption=media.caption
                        )
            except Exception as e:
                print(f"Ошибка при отправке медиа: {e}")
                await callback.message.answer(post.text or "📄 Сообщение без текста")

        await callback.answer()