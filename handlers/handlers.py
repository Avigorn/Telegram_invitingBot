import logging
from datetime import datetime, timedelta

from aiogram import F
from aiogram.enums import ContentType
from aiogram.filters import Command
from config.config import add_user, save_chat, get_users_in_chat, add_message, update_chat_data
from handlers.base_handler import BaseHandler

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State


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

class ChatSelectionStates(StatesGroup):
    SELECT_INVITING_CHAT = State()
    SELECT_INVITED_CHAT = State()

class ChatSelectionHandler(BaseHandler):
    def __init__(self, bot, dp):
        super().__init__(bot, dp)
        self.register_handlers()

    def register_handlers(self):
        # Регистрация обработчиков для callback_data="set_chats"
        self._router.callback_query(F.data == "set_chats")(self.start_chat_selection)
        self._router.callback_query(F.data.startswith("select_chat_"))(self.handle_chat_selection)

    async def start_chat_selection(self, callback: CallbackQuery):
        """Начало процесса выбора чатов"""
        await callback.message.edit_text(
            "Выберите INVITING_CHAT:",
            reply_markup=self.generate_keyboard()
        )
        await self.set_state(callback.from_user.id, ChatSelectionStates.SELECT_INVITING_CHAT)
        await callback.answer()

    async def handle_chat_selection(self, callback: CallbackQuery, state: FSMContext):
        """Обработка выбора чата из инлайн-кнопок"""
        chat_id = int(callback.data.split("_")[-1])
        current_state = await state.get_state()

        if current_state == ChatSelectionStates.SELECT_INVITING_CHAT.state:
            save_chat("INVITING_CHAT", chat_id)
            await state.update_data(inviting_chat_id=chat_id)
            await callback.message.edit_text(
                "INVITING_CHAT установлен.\nТеперь выберите INVITED_CHAT:",
                reply_markup=self.generate_keyboard()
            )
            await self.set_state(callback.from_user.id, ChatSelectionStates.SELECT_INVITED_CHAT)
        elif current_state == ChatSelectionStates.SELECT_INVITED_CHAT.state:
            data = await state.get_data()
            inviting_chat_id = data.get('inviting_chat_id')
            save_chat("INVITED_CHAT", chat_id)
            update_chat_data(inviting_chat_id, chat_id)
            await callback.message.edit_text(
                f"ID чатов установлены:\nINVITING_CHAT: {inviting_chat_id}\nINVITED_CHAT: {chat_id}"
            )
            await state.clear()
        await callback.answer()

    def generate_keyboard(self):
        """Генерация клавиатуры с доступными чатами"""
        chats = get_available_chats()  # Функция должна возвращать список чатов
        keyboard = InlineKeyboardMarkup(row_width=1)
        for chat in chats:
            keyboard.add(InlineKeyboardButton(f"{chat.id} - {chat.title}", callback_data=f"select_chat_{chat.id}"))
        return keyboard

class EventButton(BaseHandler):
    def __init__(self, bot, dp, chat_id):
        super().__init__(bot, dp)
        self.chat_id = chat_id
        self.waiting_for_event_text = {}
        self.register_handlers()

    def register_handlers(self):
        self._router.callback_query(F.data == "event")(self.handle_event)

    async def handle_event(self, callback_query):
        """Обработка кнопки Мероприятие"""
        chat_id = callback_query.message.chat.id
        if chat_id != self.chat_id:
            await callback_query.answer("Эта функция работает только в группе.")
            return

        # Получаем список пользователей из базы данных
        users = get_users_in_chat(chat_id)
        members = [f"@{username}" if username else full_name for username, full_name in users]
        mention_text = " ".join(members)

        await callback_query.message.answer(f"{callback_query.from_user.full_name}, введите текст для мероприятия:")
        self.waiting_for_event_text[callback_query.from_user.id] = {"chat_id": chat_id, "mention_text": mention_text}
        await callback_query.answer()

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
            [InlineKeyboardButton(text="Установить чаты", callback_data="set_chats")],
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
            logging.error(f"Произошла ошибка: {e}", exc_info=True)
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