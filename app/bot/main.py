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


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    logger.info("NEW CODE LOADED - DEBUG HANDLER ACTIVE")
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


async def handle_all_messages(message: Message):
    """Debug handler to log all incoming messages"""
    logger.info("Received message: type=%s, content_type=%s, web_app_data=%s", 
                type(message), getattr(message, 'content_type', None), 
                bool(getattr(message, 'web_app_data', None)))
    
    # If this message has web_app_data, handle it directly
    if hasattr(message, 'web_app_data') and message.web_app_data:
        await handle_webapp_data(message)


async def handle_all_updates(update: Update):
    """Debug handler to log all incoming updates and process web_app_data"""
    logger.info("=== UPDATE %s ===", update.update_id)
    logger.info("Update type: %s", type(update))
    
    # Log all non-None attributes
    for attr in dir(update):
        if not attr.startswith('_'):
            value = getattr(update, attr)
            if value is not None and not callable(value):
                logger.info("Update.%s = %s", attr, value)
    
    # Check message for web_app_data
    if hasattr(update, 'message') and update.message:
        msg = update.message
        logger.info("Message exists - checking for web_app_data")
        logger.info("Message type: %s", type(msg))
        
        # Log message attributes
        for attr in dir(msg):
            if not attr.startswith('_'):
                value = getattr(msg, attr)
                if value is not None and not callable(value):
                    logger.info("Message.%s = %s", attr, str(value)[:200])
        
        # Check for web_app_data
        if hasattr(msg, 'web_app_data') and msg.web_app_data:
            logger.info("FOUND WEB_APP_DATA in message!")
            await handle_webapp_data(msg)
            return
    
    # Check for inline_query with web_app
    if hasattr(update, 'inline_query') and update.inline_query:
        logger.info("Inline query detected")
    
    # Check for callback_query with web_app
    if hasattr(update, 'callback_query') and update.callback_query:
        logger.info("Callback query detected")
    
    logger.info("=== END UPDATE %s ===", update.update_id)


async def handle_webapp_data(message: Message):
    """Handle web app data from message"""
    try:
        raw = message.web_app_data.data if message.web_app_data else None
        logger.info("Processing web_app_data: %s", raw)
        payload = json.loads(raw) if raw else {}
        logger.info("Parsed payload: %s", payload)
    except Exception as e:
        logger.warning("Failed to parse web_app_data: %s", e)
        payload = {"raw": raw}

    user = message.from_user
    if user is None:
        logger.error("No user found in message")
        await message.answer("Не удалось определить пользователя.")
        return

    logger.info("User info: id=%s, username=%s, first_name=%s", user.id, user.username, user.first_name)

    # Store participant
    session_gen = get_session()
    session = next(session_gen)
    try:
        service = ParticipantService(session)
        logger.info("Creating participant service and upserting...")
        participant = service.submit_participation(
            telegram_user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code,
            is_premium=getattr(user, "is_premium", None),
            extra_data=payload,
        )
        logger.info("Participant created successfully: id=%s", participant.id)
        await message.answer("Вы успешно зарегистрированы как участник! Удачи в конкурсе.")
    except Exception as e:
        logger.error("Failed to create participant: %s", e)
        await message.answer("Произошла ошибка при регистрации. Попробуйте еще раз.")
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

    # Register handlers in order of specificity
    dp.message.register(handle_start, CommandStart())
    
    # Global update handler for debugging - this should catch everything
    dp.update.register(handle_all_updates)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main()) 