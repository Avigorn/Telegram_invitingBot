from aiogram import Router

class BaseHandler:
    def __init__(self, bot, dp):
        # Приватные поля (доступны только внутри класса)
        self.__bot = bot  # Приватное поле для бота <button class="citation-flag" data-index="4">
        self.__dp = dp    # Приватное поле для диспетчера

        # Защищенное поле (доступно внутри класса и его наследников)
        self._router = Router()  # Защищенное поле для роутера <button class="citation-flag" data-index="4">

        # Добавляем роутер в диспетчер
        self.__dp.include_router(self._router)

    # Публичный метод (доступен извне)
    def register_handlers(self):
        """
        Метод для регистрации обработчиков.
        Должен быть переопределен в дочерних классах.
        """
        raise NotImplementedError("Метод register_handlers должен быть переопределен в дочернем классе.") #<button class="citation-flag" data-index="4">

    # Геттер для приватного поля __bot
    @property
    def bot(self):
        return self.__bot

    # Геттер для приватного поля __dp
    @property
    def dp(self):
        return self.__dp