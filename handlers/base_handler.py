from aiogram import Router
from aiogram.filters import Command, F
from aiogram.types import Message, CallbackQuery

class BaseHandler:
    def __init__(self, bot, dp):
        self.bot = bot
        self.dp = dp
        self.router = Router()
        self.dp.include_router(self.router)

    def register_handlers(self):
        raise NotImplementedError("Метод register_handlers должен быть переопределен в дочернем классе.")