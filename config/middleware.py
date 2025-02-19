from collections import defaultdict, deque
from datetime import datetime, timedelta

from aiogram import BaseMiddleware


class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        # Словарь для хранения очередей запросов пользователей
        self.user_request_times = defaultdict(lambda: deque(maxlen=50))

    async def __call__(self, handler, event, data):
        user_id = event.from_user.id
        current_time = datetime.now()

        # Удаляем старые записи (старше 60 секунд)
        while self.user_request_times[user_id] and self.user_request_times[user_id][0] < current_time - timedelta(seconds=60):
            self.user_request_times[user_id].popleft()

        # Проверяем количество запросов за последние 60 секунд
        if len(self.user_request_times[user_id]) >= 5:
            await event.answer("Слишком много запросов! Пожалуйста, подождите.")
            return

        # Добавляем текущий запрос в очередь (очередь хранит максимум 50 записей)
        self.user_request_times[user_id].append(current_time)

        # Передаем управление следующему обработчику
        return await handler(event, data)