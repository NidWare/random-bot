from __future__ import annotations

import asyncio
import json
import logging
from urllib.parse import urlparse
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, WebAppInfo, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

from app.config import settings
from app.db.base import init_db, get_session
from app.services.participant_service import ParticipantService


logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    init_db()
    # Ensure polling receives updates even if a webhook was previously set
    try:
        await bot.delete_webhook(drop_pending_updates=False)
    except Exception as e:
        logger.warning("delete_webhook failed: %s", e)
    me = await bot.get_me()
    logger.info("Bot started as @%s", me.username)


def build_start_keyboard() -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    parsed = urlparse(settings.WEBAPP_URL)
    if parsed.scheme == "https":
        kb.button(text="Открыть Mini App", web_app=WebAppInfo(url=settings.WEBAPP_URL))
    else:
        # Fallback to a regular URL button to avoid Telegram BadRequest
        kb.row(InlineKeyboardButton(text="Открыть сайт (нужен HTTPS для Mini App)", url=settings.WEBAPP_URL))
    kb.adjust(1)
    return kb


async def handle_start(message: Message):
    notice = ""
    if not urlparse(settings.WEBAPP_URL).scheme == "https":
        notice = "\n\nВнимание: для Mini App нужен HTTPS. Админ, обнови WEBAPP_URL."
    await message.answer(
        "Привет! Нажмите кнопку ниже, чтобы подтвердить участие в конкурсе." + notice,
        reply_markup=build_start_keyboard().as_markup(),
    )


async def handle_webapp_data(message: Message):
    # message.web_app_data.data contains a string
    try:
        payload = json.loads(message.web_app_data.data)
    except Exception:
        payload = {"raw": message.web_app_data.data}

    user = message.from_user
    if user is None:
        await message.answer("Не удалось определить пользователя.")
        return

    # Store participant
    session_gen = get_session()
    session = next(session_gen)
    try:
        service = ParticipantService(session)
        service.submit_participation(
            telegram_user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code,
            is_premium=getattr(user, "is_premium", None),
            extra_data=payload,
        )
        await message.answer("Вы успешно зарегистрированы как участник! Удачи в конкурсе.")
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass


async def main():
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.startup.register(on_startup)

    dp.message.register(handle_start, CommandStart())
    dp.message.register(handle_webapp_data, F.web_app_data)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main()) 