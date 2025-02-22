import logging
import sqlite3
from aiogram.types import ChatMember
from logger import setup_logger

logger = setup_logger()

# Подключение к базе данных
def connect_db():
    return sqlite3.connect("identifier.sqlite")

def create_tables():
    connection = connect_db()
    cursor = connection.cursor()

    # Таблица для хранения ID чатов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_type TEXT NOT NULL, -- INVITING_CHAT или INVITED_CHAT
            chat_id INTEGER NOT NULL UNIQUE
        )
        """)

    # Таблица для хранения пользователей с внешним ключом на таблицу chats
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS users (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           user_id INTEGER NOT NULL UNIQUE,
           username TEXT,
           full_name TEXT,
           joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
           chat_id INTEGER,
           FOREIGN KEY(chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE
       )
       """)

    # Таблица для хранения пользователей
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        username TEXT,
        full_name TEXT,
        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Таблица для хранения сообщений
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message_text TEXT,
        sent_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Таблица для отслеживания активности пользователей
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        request_time DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    connection.commit()
    connection.close()

# Загрузка конфигурации
def load_config():
    connection = connect_db()
    cursor = connection.cursor()

    # Загрузка ID чатов
    cursor.execute("SELECT chat_type, chat_id FROM chats")
    chats = {row[0]: row[1] for row in cursor.fetchall()}

    connection.close()
    return chats

# Сохранение ID чата
def save_chat(chat_type, chat_id):
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("INSERT OR REPLACE INTO chats (chat_type, chat_id) VALUES (?, ?)", (chat_type, chat_id))
    connection.commit()
    connection.close()

# Добавление пользователя в базу данных
def add_user(user_id, username, full_name, chat_id):
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("""
    INSERT OR IGNORE INTO users (user_id, username, full_name, chat_id)
    VALUES (?, ?, ?, ?)
    """, (user_id, username, full_name, chat_id))
    connection.commit()
    connection.close()

# Добавление сообщения в базу данных
def add_message(user_id, message_text):
    connection = connect_db()
    cursor = connection.cursor()

    # Добавляем новое сообщение
    cursor.execute("""
    INSERT INTO messages (user_id, message_text)
    VALUES (?, ?)
    """, (user_id, message_text))

    # Удаляем старые сообщения, если их больше 100
    cursor.execute("""
    DELETE FROM messages
    WHERE id NOT IN (
        SELECT id FROM messages
        ORDER BY sent_at DESC
        LIMIT 100
    )
    """)

    connection.commit()
    connection.close()

# Запись активности пользователя
# Запись активности пользователя с ограничением до 50 записей
def log_user_activity(user_id):
    connection = connect_db()
    cursor = connection.cursor()

    try:
        # Добавляем новую запись о запросе пользователя
        cursor.execute("""
        INSERT INTO user_activity (user_id)
        VALUES (?)
        """, (user_id,))

        # Удаляем старые записи, если их больше 50 для данного пользователя
        cursor.execute("""
        DELETE FROM user_activity
        WHERE id NOT IN (
            SELECT id
            FROM user_activity
            WHERE user_id = ?
            ORDER BY request_time DESC
            LIMIT 50
        )
        """, (user_id,))

        connection.commit()
    except Exception as e:
        logging.error(f"Ошибка при записи активности пользователя: {e}")
    finally:
        connection.close()

# Добавление функции для проверки и очистки неактивных пользователей
def cleanup_inactive_users():
    connection = connect_db()
    cursor = connection.cursor()

    # Удаляем пользователей, которые больше не являются участниками чатов
    cursor.execute("""
    DELETE FROM users 
    WHERE chat_id NOT IN (SELECT chat_id FROM chats)
    """)

    connection.commit()
    connection.close()


# Получение всех пользователей из чата
def get_users_in_chat(chat_id):
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("SELECT username, full_name FROM users WHERE chat_id = ?", (chat_id,))
    users = cursor.fetchall()
    connection.close()
    return users

# Добавление функции для обновления данных о чатах
def update_chat_data(inviting_chat_id, invited_chat_id):
    connection = connect_db()
    cursor = connection.cursor()

    # Обновляем chat_id для всех пользователей
    cursor.execute("""
    UPDATE users
    SET chat_id = ?
    WHERE chat_id = ?
    """, (inviting_chat_id, invited_chat_id))

    connection.commit()
    connection.close()

async def add_existing_users_to_db(bot, chat_id):
    """Добавление существующих пользователей из чата в базу данных"""
    connection = connect_db()

    try:
        # Получаем список участников чата через Telegram API
        users = await get_chat_members(bot, chat_id)  # Используем await для асинхронного вызова
        for user in users:
            add_user(
                user_id=user.user.id,  # Обратите внимание на user.user (для объекта ChatMember)
                username=user.user.username,
                full_name=user.user.full_name,
                chat_id=chat_id
            )
        connection.commit()
    except Exception as e:
        logger.exception(f"Ошибка при добавлении существующих пользователей: {e}")
    finally:
        connection.close()


from aiogram.types import ChatMember

async def get_chat_members(bot, chat_id):
    """Получение списка участников чата"""
    members = []
    try:
        # Получаем общее количество участников
        total_members = await bot.get_chat_member_count(chat_id)
        offset = 0
        limit = 200  # Максимальное количество участников за один запрос

        while offset < total_members:
            # Telegram API не предоставляет прямой метод для получения всех участников,
            # поэтому мы будем получать их через итерацию
            chunk = []  # Здесь будет храниться порция участников
            for user_id in range(offset, min(offset + limit, total_members)):
                try:
                    member = await bot.get_chat_member(chat_id, user_id)
                    if isinstance(member, ChatMember) and member.status != "left":
                        chunk.append(member)
                except Exception as e:
                    logger.error(f"Ошибка при получении участника с ID {user_id}: {e}", exc_info=True)
            members.extend(chunk)
            offset += limit
    except Exception as e:
        logger.error(f"Ошибка при получении участников чата: {e}", exc_info=True)
    return members