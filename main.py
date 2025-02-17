import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from config.middleware import AntiSpamMiddleware
from handlers.handlers import StartHandler, HelpButton, InviteButton, EventButton, DepartureHandler, NewMemberHandler, ChatSelectionHandler, MessageHandler
from config.config import load_config

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загрузка конфигурации
try:
    chats = load_config()
    INVITING_CHAT_ID = chats.get("INVITING_CHAT")
    INVITED_CHAT_ID = chats.get("INVITED_CHAT")
except Exception as e:
    print(f"Ошибка загрузки конфигурации: {e}")
    INVITING_CHAT_ID = None
    INVITED_CHAT_ID = None

# Инициализация бота
session = AiohttpSession(proxy="http://proxy.server:3128")
token = load_config()
bot = Bot(token=token, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

dp.message.middleware(AntiSpamMiddleware())

# Инициализация обработчиков
start_handler = StartHandler(bot, dp)
help_button = HelpButton(bot, dp, INVITED_CHAT_ID)
invite_button = InviteButton(bot, dp, INVITING_CHAT_ID, INVITED_CHAT_ID)
event_button = EventButton(bot, dp, INVITED_CHAT_ID)
departure_handler = DepartureHandler(bot, dp, INVITED_CHAT_ID)
new_member_handler = NewMemberHandler(bot, dp)
chat_selection_handler = ChatSelectionHandler(bot, dp)
message_handler = MessageHandler(bot, dp)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())