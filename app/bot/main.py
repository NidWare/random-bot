from __future__ import annotations

import asyncio
import json
import logging
from urllib.parse import urlparse
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, WebAppInfo, InlineKeyboardButton, Update
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
        raw = message.web_app_data.data if message.web_app_data else None
        logger.info("Received web_app_data: %s", raw)
        payload = json.loads(raw) if raw else {}
    except Exception as e:
        logger.warning("Failed to parse web_app_data: %s", e)
        payload = {"raw": raw}

    user = message.from_user
    if user is None:
        await message.answer("Не удалось определить пользователя.")
        return

    # Store participant
    session_gen = get_session()
    session = next(session_gen)
    try:
        service = ParticipantService(session)
        logger.info("Upserting participant id=%s username=%s", user.id, user.username)
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


async def handle_all_messages(message: Message):
    """Debug handler to log all incoming messages"""
    logger.info("Received message: type=%s, content_type=%s, web_app_data=%s", 
                type(message), getattr(message, 'content_type', None), 
                bool(getattr(message, 'web_app_data', None)))
    
    # If this message has web_app_data, handle it directly
    if hasattr(message, 'web_app_data') and message.web_app_data:
        await handle_webapp_data(message)


async def handle_all_updates(update: Update):
    """Debug handler to log all incoming updates"""
    logger.info("Received update: id=%s, type=%s", update.update_id, type(update))
    
    # Check for web_app_data in message
    if hasattr(update, 'message') and update.message and hasattr(update.message, 'web_app_data'):
        logger.info("Found web_app_data in message")
        await handle_webapp_data(update.message)
        return
    
    # Check for web_app_data in other update types
    if hasattr(update, 'web_app_data'):
        logger.info("Found web_app_data in update directly")
    
    # Log all attributes of the update for debugging
    attrs = [attr for attr in dir(update) if not attr.startswith('_') and getattr(update, attr) is not None]
    logger.info("Update attributes: %s", attrs)
    
    # If it's a message, log its type and content
    if hasattr(update, 'message') and update.message:
        msg = update.message
        logger.info("Message content_type: %s, text: %s, web_app_data: %s", 
                   getattr(msg, 'content_type', None), 
                   getattr(msg, 'text', None)[:50] if getattr(msg, 'text', None) else None,
                   bool(getattr(msg, 'web_app_data', None)))


async def main():
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.startup.register(on_startup)

    dp.message.register(handle_start, CommandStart())
    # Handle both explicit web_app_data updates and any message containing web_app_data
    dp.message.register(handle_webapp_data, F.web_app_data)
    # Universal handler for debugging (should be last)
    dp.message.register(handle_all_messages)
    
    # Global update handler for debugging - this should catch everything
    dp.update.register(handle_all_updates)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main()) 