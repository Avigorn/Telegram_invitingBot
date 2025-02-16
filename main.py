import asyncio
import logging
from aiogram import Bot, Dispatcher
from config.config import OWNER_ID, INVITING_CHAT_ID, INVITED_CHAT_ID
from handlers.handlers import StartHandler, HelpButton, InviteButton, EventButton, DepartureHandler, StopHandler

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token="YOUR_BOT_TOKEN")
dp = Dispatcher()

# Инициализация обработчиков
start_handler = StartHandler(bot, dp)
help_button = HelpButton(bot, dp, INVITED_CHAT_ID)
invite_button = InviteButton(bot, dp, INVITING_CHAT_ID, INVITED_CHAT_ID)
event_button = EventButton(bot, dp, INVITED_CHAT_ID)
departure_handler = DepartureHandler(bot, dp, INVITED_CHAT_ID)
stop_handler = StopHandler(bot, dp, OWNER_ID)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())