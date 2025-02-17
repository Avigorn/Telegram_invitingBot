import sqlite3

# Подключение к базе данных
def connect_db():
    return sqlite3.connect("identifier.sqlite")

# Загрузка конфигурации
def load_config():
    connection = connect_db()
    cursor = connection.cursor()

    # Загрузка ID чатов
    cursor.execute("SELECT chat_type, chat_id FROM chats")
    chats = {row[0]: row[1] for row in cursor.fetchall()}

    # Загрузка токена бота
    cursor.execute("SELECT token FROM bot_token LIMIT 1")
    token = cursor.fetchone()[0]

    connection.close()
    return token, chats

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
