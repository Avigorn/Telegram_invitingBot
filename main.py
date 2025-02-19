import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from config.middleware import AntiSpamMiddleware
from handlers.handlers import StartHandler, HelpButton, InviteButton, EventButton, DepartureHandler, NewMemberHandler, ChatSelectionHandler, MessageHandler
from config.config import load_config, add_existing_users_to_db
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)

load_dotenv()

# Загрузка конфигурации
try:
    chats= load_config()
    INVITING_CHAT_ID = chats.get("INVITING_CHAT")
    INVITED_CHAT_ID = chats.get("INVITED_CHAT")
except Exception as e:
    print(f"Ошибка загрузки конфигурации: {e}")
    INVITING_CHAT_ID = None
    INVITED_CHAT_ID = None

# Инициализация бота
session = AiohttpSession(proxy="http://proxy.server:3128")
bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'), session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

dp.message.middleware(AntiSpamMiddleware())
dp.callback_query.middleware(AntiSpamMiddleware())  # Добавляем middleware для callback-запросов

# Инициализация обработчиков
start_handler = StartHandler(bot, dp)
help_button = HelpButton(bot, dp)
invite_button = InviteButton(bot, dp, INVITING_CHAT_ID, INVITED_CHAT_ID)
event_button = EventButton(bot, dp, INVITED_CHAT_ID)
departure_handler = DepartureHandler(bot, dp, INVITED_CHAT_ID)
new_member_handler = NewMemberHandler(bot, dp)
chat_selection_handler = ChatSelectionHandler(bot, dp)
message_handler = MessageHandler(bot, dp)

async def main():
    # Добавляем существующих пользователей из чатов в базу данных
    if INVITING_CHAT_ID:
        await asyncio.to_thread(add_existing_users_to_db, INVITING_CHAT_ID)
    if INVITED_CHAT_ID:
        await asyncio.to_thread(add_existing_users_to_db, INVITED_CHAT_ID)

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())