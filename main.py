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

# Инициализация бота
session = AiohttpSession(proxy="http://proxy.server:3128")
token, chats = load_config()
bot = Bot(token=token, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

dp.message.middleware(AntiSpamMiddleware())

# Инициализация обработчиков
start_handler = StartHandler(bot, dp)
help_button = HelpButton(bot, dp, chats["INVITED_CHAT"])
invite_button = InviteButton(bot, dp, chats["INVITING_CHAT"], chats["INVITED_CHAT"])
event_button = EventButton(bot, dp, chats["INVITED_CHAT"])
departure_handler = DepartureHandler(bot, dp, chats["INVITED_CHAT"])
new_member_handler = NewMemberHandler(bot, dp)
chat_selection_handler = ChatSelectionHandler(bot, dp)
message_handler = MessageHandler(bot, dp)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())