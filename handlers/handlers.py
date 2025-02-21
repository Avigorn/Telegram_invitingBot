import logging
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.enums import ContentType
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.markdown import hlink

from config.config import add_user, save_chat, add_message, update_chat_data, logger
from handlers.base_handler import BaseHandler
from aiogram.enums import ParseMode


class NewMemberHandler(BaseHandler):
    def __init__(self, bot, dp):
        super().__init__(bot, dp)
        self.register_handlers()

    def register_handlers(self):
        self._router.chat_member()(self.handle_new_member)

    async def handle_new_member(self, event):
        """Обработка добавления нового участника"""
        new_member = event.new_chat_member.user
        chat_id = event.chat.id

        # Добавляем пользователя в базу данных
        add_user(
            user_id=new_member.id,
            username=new_member.username,
            full_name=new_member.full_name,
            chat_id=chat_id
        )
        logging.info(f"User {new_member.full_name} added to chat {chat_id}")  # Добавлено логирование

        # Приветствуем нового участника
        await self.bot.send_message(
            chat_id=chat_id,
            text=f"Приветствую, {new_member.full_name}! Добро пожаловать!"
        )

class ChatSelectionHandler(BaseHandler):
    def __init__(self, bot, dp):
        super().__init__(bot, dp)
        self.register_handlers()

    def register_handlers(self):
        self._router.message(Command("set_chats"))(self.set_chats)

    async def set_chats(self, message):
        """Установка ID чатов через команду"""
        try:
            inviting_chat_id, invited_chat_id = map(int, message.text.split()[1:])
            save_chat("INVITING_CHAT", inviting_chat_id)
            save_chat("INVITED_CHAT", invited_chat_id)

            update_chat_data(inviting_chat_id, invited_chat_id)

            await message.answer(f"ID чатов установлены:\nINVITING_CHAT: {inviting_chat_id}\nINVITED_CHAT: {invited_chat_id}")
        except (IndexError, ValueError):
            await message.answer("Используйте формат: /set_chats <INVITING_CHAT_ID> <INVITED_CHAT_ID>")

from aiogram import F, types

class EventButton(BaseHandler):
    def __init__(self, bot, dp, chat_id):
        super().__init__(bot, dp)
        self.chat_id = chat_id
        self.waiting_for_event_text = {}
        self.register_handlers()

    def register_handlers(self):
        # Регистрируем обработчик для кнопки "Мероприятие"
        self._router.callback_query(F.data == "event")(self.handle_event)
        # Регистрируем обработчик для получения текста мероприятия
        self._router.message()(self.send_event_announcement)

    async def handle_event(self, callback_query: types.CallbackQuery):
        """Обработка кнопки 'Мероприятие'"""
        chat_id = callback_query.message.chat.id
        if chat_id != self.chat_id:
            await callback_query.answer("Эта функция работает только в группе.")
            return

        # Запрашиваем у пользователя текст объявления
        await callback_query.message.answer(f"{callback_query.from_user.full_name}, введите текст для мероприятия:")
        self.waiting_for_event_text[callback_query.from_user.id] = {"chat_id": chat_id}
        await callback_query.answer()

    async def send_event_announcement(self, message: types.Message):
        """Отправка объявления о мероприятии со всеми упоминаниями"""
        user_id = message.from_user.id

        # Проверяем, ждем ли мы текст объявления от этого пользователя
        if user_id not in self.waiting_for_event_text:
            return

        chat_id = self.waiting_for_event_text[user_id]["chat_id"]
        announcement_text = message.text

        try:
            # Вызываем функцию mention_all для отметки всех участников
            await mention_all(chat_id, self.bot, announcement_text)
            await message.answer("Объявление отправлено!")
        except Exception as e:
            logger.error(f"Ошибка при отправке объявления: {e}")
            await message.answer("Не удалось отправить объявление. Попробуйте снова.")

        # Удаляем ожидание текста от пользователя
        del self.waiting_for_event_text[user_id]

class StartHandler(BaseHandler):
    def __init__(self, bot, dp):
        super().__init__(bot, dp)
        self.register_handlers()

    def register_handlers(self):
        # Регистрация обработчиков через защищенный роутер
        self._router.message(Command("start"))(self.cmd_start)

    async def cmd_start(self, message):
        """Обработка команды /start"""
        await self.bot.send_message(
            chat_id=message.chat.id,
            text="Приветствую тебя, Шарьинец! Прочитайте описание или воспользуйтесь кнопкой Помощь:"
        )
        kb = [
            [InlineKeyboardButton(text="Помощь", callback_data="help")],
            [InlineKeyboardButton(text="Приглашение", callback_data="invite")],
            [InlineKeyboardButton(text="Мероприятие", callback_data="event")],
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
        await self.bot.send_message(chat_id=message.chat.id, text="Выберите одну из опций:", reply_markup=keyboard)

class HelpButton(BaseHandler):
    def __init__(self, bot, dp):
        super().__init__(bot, dp)
        self.register_handlers()

    def register_handlers(self):
        self._router.callback_query(F.data == "help")(self.handle_help)

    async def handle_help(self, callback_query):
        """Обработка кнопки Помощь"""
        await callback_query.message.answer(
            "Список моих возможностей:\n"
            "• Приглашение - получить пригласительную ссылку\n"
            "• Мероприятие - отметить всех и указать причину\n"
            "• Сообщение 'Я уехал' - временно покинуть группу"
        )
        await callback_query.answer()  # Подтверждаем получение запроса

class InviteButton(BaseHandler):
    def __init__(self, bot, dp, inviting_chat_id, invited_chat_id):
        super().__init__(bot, dp)
        self.inviting_chat_id = inviting_chat_id
        self.invited_chat_id = invited_chat_id
        self.register_handlers()

    def register_handlers(self):
        self.router.callback_query(F.data == "invite")(self.handle_invite)

    async def handle_invite(self, callback_query):
            """Обработка кнопки Приглашение"""
            user_id = callback_query.from_user.id
            try:
                # Проверяем права бота в чате
                bot_member = await self.bot.get_chat_member(chat_id=self.inviting_chat_id, user_id=self.bot.id)
                if bot_member.status not in ["administrator", "creator"]:
                    await self.bot.send_message(chat_id=user_id,
                                                text="Бот не имеет прав для создания пригласительной ссылки.")
                    return

                chat_member = await self.bot.get_chat_member(chat_id=self.inviting_chat_id, user_id=user_id)
                if chat_member.status not in ["member", "administrator", "creator"]:
                    await self.bot.send_message(chat_id=user_id, text="Вы не состоите в группе.")
                    return

                link = await self.bot.create_chat_invite_link(chat_id=self.invited_chat_id, member_limit=1)
                await self.bot.send_message(chat_id=user_id, text=f"Милости прошу к нашему шалашу: {link.invite_link}")
            except Exception as e:
                logging.error(f"Произошла ошибка: {e}")
            await callback_query.answer()  # Подтверждаем получение запроса

class DepartureHandler(BaseHandler):
    def __init__(self, bot, dp, chat_id):
        super().__init__(bot, dp)
        self.chat_id = chat_id
        self.register_handlers()

    def register_handlers(self):
        self.router.message(F.text.lower() == "я уехал")(self.handle_departure)

    async def handle_departure(self, message):
        """Обработка сообщения 'Я уехал'"""
        user_id = message.from_user.id
        chat_id = message.chat.id

        if chat_id != self.chat_id:
            await message.reply("Эта команда не работает в данной группе.")
            return

        try:
            if message.content_type in [ContentType.PHOTO, ContentType.VIDEO, ContentType.DOCUMENT]:
                await message.copy_to(chat_id=self.chat_id, caption=f"Пользователь {message.from_user.full_name} отправил это перед выходом.")

            until_date = datetime.now() + timedelta(minutes=1)
            await self.bot.ban_chat_member(chat_id=chat_id, user_id=user_id, until_date=until_date)
            await self.bot.send_message(chat_id=self.chat_id, text=f"Уважаемый {message.from_user.full_name} сообщил, что уехал, и был временно исключен из группы.")
            await self.bot.send_message(chat_id=user_id, text="Вы были временно исключены из группы.")
        except Exception as e:
            logging.error(f"Произошла ошибка: {e}")
            await message.reply("Не удалось исключить пользователя. Попробуйте позже.")

class MessageHandler(BaseHandler):
    def __init__(self, bot, dp):
        super().__init__(bot, dp)
        self.register_handlers()

    def register_handlers(self):
        self._router.message()(self.handle_message)

    async def handle_message(self, message):
        """Обработка текстовых сообщений"""
        user_id = message.from_user.id
        message_text = message.text

        # Добавляем сообщение в базу данных
        add_message(user_id, message_text)

async def mention_all(chat_id: int, bot: Bot, message_text: str):
    try:
        # Получаем список всех участников чата
        members = []
        member_count = await bot.get_chat_member_count(chat_id)
        for i in range(0, member_count):
            try:
                member = await bot.get_chat_member(chat_id, i)
                if member.user.is_bot or member.status in ["left", "kicked"]:
                    continue  # Пропускаем ботов и тех, кто покинул чат
                members.append(member.user)
            except Exception as e:
                continue  # Если не удается получить информацию о пользователе

        # Формируем сообщение с упоминаниями
        full_message = f"{message_text}\n\n"
        for user in members:
            if user.username:
                mention = f"@{user.username}"
            else:
                mention = hlink(title=user.full_name, url=f"tg://user?id={user.id}")
            full_message += f"{mention} "

            # Проверяем длину сообщения (максимум 4096 символов)
            if len(full_message) > 3500:  # Оставляем место для безопасного завершения сообщения
                await bot.send_message(chat_id, full_message, parse_mode=ParseMode.HTML)
                full_message = ""  # Начинаем новое сообщение

        # Отправляем последнее сообщение, если оно не пустое
        if full_message:
            await bot.send_message(chat_id, full_message, parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.exception(f"Ошибка при отметке всех пользователей: {e}")