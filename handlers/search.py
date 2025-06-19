from aiogram import Router, types, F
from database.crud import search_posts_by_hashtag, increment_hashtag_counter
from database.session import async_session

router = Router()


@router.callback_query(F.data.startswith("hashtag:"))
async def show_hashtag_posts(callback: types.CallbackQuery):
    hashtag = callback.data.split(":")[1]

    async with async_session() as session:
        # Увеличиваем счётчик
        await increment_hashtag_counter(session, hashtag)

        # Ищем посты
        posts = await search_posts_by_hashtag(session, hashtag)

        if not posts:
            await callback.message.answer(f"По рубрике {hashtag} пока нет публикаций.")
            return

        # Ограничиваем вывод (например, 5 последних постов)
        for post in posts[:5]:
            await callback.message.answer(post.text)

        await callback.answer()