import sqlite3

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
    """
# Запись активности пользователя
def log_user_activity(user_id):
    connection = connect_db()
    cursor = connection.cursor()

    # Добавляем запись о запросе пользователя
    cursor.execute("""
    #INSERT INTO user_activity (user_id)
    #VALUES (?)
    """, (user_id,))
    connection.commit()
    connection.close()
    """


# Получение всех пользователей из чата
def get_users_in_chat(chat_id):
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("SELECT username, full_name FROM users WHERE chat_id = ?", (chat_id,))
    users = cursor.fetchall()
    connection.close()
    return users
