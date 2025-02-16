import logging

from aiogram import F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from base_handler import BaseHandler
from datetime import datetime, timedelta
from aiogram.enums import ContentType

class StartHandler(BaseHandler):
    def __init__(self, bot, dp):
        super().__init__(bot, dp)
        self.register_handlers()

    def register_handlers(self):
        self.router.message(Command("start"))(self.cmd_start)

    async def cmd_start(self, message):
        """Обработка команды /start"""
        await message.answer("Приветствую тебя, Шарьинец! Прочитайте описание или воспользуйтесь кнопкой Помощь:")
        kb = [
            [InlineKeyboardButton(text="Помощь", callback_data="help")],
            [InlineKeyboardButton(text="Приглашение", callback_data="invite")],
            [InlineKeyboardButton(text="Мероприятие", callback_data="event")],
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
        await message.answer("Выберите одну из опций:", reply_markup=keyboard)


class HelpButton(BaseHandler):
    def __init__(self, bot, dp, chat_id):
        super().__init__(bot, dp)
        self.chat_id = chat_id
        self.register_handlers()

    def register_handlers(self):
        self.router.callback_query(F.data == "help")(self.handle_help)

    async def handle_help(self, callback_query):
        """Обработка кнопки Помощь"""
        await callback_query.message.answer(
            "Список моих возможностей:\n"
            "Приглашение - получить пригласительную ссылку\n"
            'Мероприятие - отметить всех и указать причину\n'
            "Сообщение содержащее Я уехал - временно покинуть группу"
        )
        await callback_query.answer()

from base_handler import BaseHandler

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
            chat_member = await self.bot.get_chat_member(chat_id=self.inviting_chat_id, user_id=user_id)
            if chat_member.status not in ["member", "administrator", "creator"]:
                await self.bot.send_message(chat_id=user_id, text="Вы не состоите в группе.")
                return

            link = await self.bot.create_chat_invite_link(chat_id=self.invited_chat_id, member_limit=1)
            await self.bot.send_message(chat_id=user_id, text=f"Милости прошу к нашему шалашу: {link.invite_link}")
        except Exception as e:
            logging.error(f"Произошла ошибка: {e}")
        await callback_query.answer()

from base_handler import BaseHandler

class EventButton(BaseHandler):
    def __init__(self, bot, dp, chat_id):
        super().__init__(bot, dp)
        self.chat_id = chat_id
        self.waiting_for_event_text = {}
        self.register_handlers()

    def register_handlers(self):
        self.router.callback_query(F.data == "event")(self.handle_event)
        self.router.message()(self.handle_event_message)

    async def handle_event(self, callback_query):
        """Обработка кнопки Мероприятие"""
        chat_id = callback_query.message.chat.id
        if chat_id != self.chat_id:
            await callback_query.answer("Эта функция работает только в группе.")
            return

        members = []
        async for member in self.bot.get_chat_members(chat_id=chat_id):
            if not member.user.is_bot and member.user.id != callback_query.from_user.id:
                members.append(f"@{member.user.username}" if member.user.username else member.user.full_name)

        mention_text = " ".join(members)
        await callback_query.message.answer(f"{callback_query.from_user.full_name}, введите текст для мероприятия:")
        self.waiting_for_event_text[callback_query.from_user.id] = {"chat_id": chat_id, "mention_text": mention_text}
        await callback_query.answer()

    async def handle_event_message(self, message):
        """Обработка текста мероприятия"""
        user_id = message.from_user.id
        if user_id in self.waiting_for_event_text:
            event_data = self.waiting_for_event_text.pop(user_id)
            if message.chat.id != event_data["chat_id"]:
                await message.reply("Пожалуйста, введите текст в правильной группе.")
                return

            event_message = message.text
            mention_text = event_data["mention_text"]
            await self.bot.send_message(chat_id=event_data["chat_id"], text=f"{mention_text}\n\n{event_message}")


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


class StopHandler(BaseHandler):
    def __init__(self, bot, dp, owner_id):
        super().__init__(bot, dp)
        self.owner_id = owner_id
        self.register_handlers()

    def register_handlers(self):
        self.router.message(Command("stop"))(self.handle_stop)

    async def handle_stop(self, message):
        """Обработка команды /stop"""
        if message.from_user.id == self.owner_id:
            await self.bot.send_message(chat_id=message.from_user.id, text="Бот останавливается...")
            await self.dp.stop_polling()
            await self.bot.session.close()
        else:
            await self.bot.send_message(chat_id=message.from_user.id, text="Только владелец может остановить бота.")