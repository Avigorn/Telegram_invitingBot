from aiogram.enums import ParseMode
from aiogram.utils.markdown import bold
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession


# Инициализация бота и диспетчера
session = AiohttpSession(proxy="protocol://host:port/")
bot = Bot(token='7558541484:AAHU9gdbOrZkesOjyUVx1IpEN2evuMiI0LU', parse_mode=ParseMode.HTML, session=session)
dp = Dispatcher()

# Создание роутера для обработки команд
router = Router()
dp.include_router(router)

# Обработчик команды /start
@router.message(Command("start"))
async def start_command(message: Message):
    await message.answer('Заходи не бойся - выходи не плачь, я бот-ассистент. Напиши /help, узнай что я могу')

# Обработчик команды /help
@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer('Список моих возможностей:\n'
                         '/start - начать диалог\n'
                         '/invite - получить приглашение\n'
                         '/stop - остановить Шарьинца')

# Обработчик команды /invite
@router.message(Command("invite"))
async def invite_command(message: Message):
    chat_id = message.chat.id
    if chat_id == -1001860031189:
        await message.answer('Это мой шалаш, он не для вас!')
    else:
        # Создание ссылки для приглашения
        link = await bot.create_chat_invite_link(chat_id=-1001860031189, member_limit=1)
        await message.answer(f'Милости прошу к нашему шалашу {link.invite_link}')


# Обработчик сообщения "Я уехал"
@router.message(F.text.lower() == ['я уехал', 'мы уехали'])
async def handle_departure_message(message: Message):
    target_group_id = -1001860031189

    # Отправляем сообщение в целевую группу
    await bot.send_message(target_group_id,
                           f"Пользователь {message.from_user.full_name} (ID: {message.from_user.id}) сообщил, что уехал.")

    # Кикаем пользователя из текущей группы
    current_chat_id = message.chat.id
    user_id = message.from_user.id
    try:
        await bot.ban_chat_member(chat_id=current_chat_id,
                                  user_id=user_id, revoke_messages=False)
        await message.reply("Вы были успешно удалены из чата, так как сообщили о своем отъезде.")
    except Exception as e:
        await message.reply(f"Не удалось вас исключить из чата. Возможно, у бота недостаточно прав. Ошибка: {e}")

# Обработчик команды /stop для остановки бота
@router.message(Command("stop"))
async def stop_bot(message: Message):
    await message.answer(bold("Бот останавливается..."), parse_mode=ParseMode.MARKDOWN)
    # Остановка поллинга
    await dp.stop_polling()  # Остановка процесса получения обновлений
    await bot.session.close()  # Закрытие сессии бота
    await message.bot.close()  # Закрытие бота


# Запуск бота
if __name__ == '__main__':
    try:
        dp.run_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        print("Бот был остановлен.")
        raise,