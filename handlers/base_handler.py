from aiogram import Router

class BaseHandler:
    def __init__(self, bot, dp):
        self.__bot = bot  # Приватное поле для бота
        self.__dp = dp    # Приватное поле для диспетчера
        self._router = Router()  # Защищенное поле для роутера
        self.__dp.include_router(self._router)

    @property
    def bot(self):
        return self.__bot

    @property
    def dp(self):
        return self.__dp

    @property
    def router(self):
        return self._router

    def register_handlers(self):
        raise NotImplementedError("Метод register_handlers должен быть переопределен в дочернем классе.")