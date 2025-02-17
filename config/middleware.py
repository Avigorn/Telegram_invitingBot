from aiogram import BaseMiddleware
from aiogram.types import Message
from datetime import datetime, timedelta
from config import connect_db

class AntiSpamMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        user_id = event.from_user.id

        # Подключение к базе данных
        connection = connect_db()
        cursor = connection.cursor()

        # Удаляем старые записи (старше 60 секунд)
        cursor.execute("""
        DELETE FROM user_activity
        WHERE request_time < datetime('now', '-60 seconds')
        """)

        # Подсчитываем количество запросов за последние 60 секунд
        cursor.execute("""
        SELECT COUNT(*) FROM user_activity
        WHERE user_id = ? AND request_time > datetime('now', '-60 seconds')
        """, (user_id,))
        count = cursor.fetchone()[0]

        # Если запросов больше 5 — считаем это спамом
        if count >= 5:
            connection.close()
            await event.answer("Слишком много запросов! Пожалуйста, подождите.")
            return

        # Добавляем новый запрос
        cursor.execute("""
        INSERT INTO user_activity (user_id)
        VALUES (?)
        """, (user_id,))
        connection.commit()
        connection.close()

        # Передаем управление следующему обработчику
        return await handler(event, data)