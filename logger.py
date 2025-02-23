import logging
from logging.handlers import RotatingFileHandler

def setup_logger():
    # Создание основного логгера
    logger = logging.getLogger('project_logger')
    logger.setLevel(logging.DEBUG)  # Уровень DEBUG позволит логировать всё

    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Только INFO и выше в консоль

    # Обработчик для записи в файл
    file_handler = RotatingFileHandler('app.log', maxBytes=1024*1024*5, backupCount=3)
    file_handler.setLevel(logging.DEBUG)  # Все уровни в файл

    # Форматирование логов для консоли
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # Форматирование логов для файла с добавлением traceback
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(exc_info)s')
    file_handler.setFormatter(file_formatter)

    # Добавление обработчиков к логгеру
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger