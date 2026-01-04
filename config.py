import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

# Основные настройки бота
TOKEN = os.getenv("BOT_TOKEN")  # Токен из .env
BOT_TOKEN = TOKEN  # Добавляем алиас для совместимости с импортом в main.py

# Список ID администраторов (поддержка нескольких через запятую)
ADMIN_IDS = set(map(int, os.getenv("ADMIN_IDS", "8287615700").split(",")))

# Курс обмена: KRW → RUB (по умолчанию 0.072)
EXCHANGE_RATE = float(os.getenv("EXCHANGE_RATE", "0.072"))

# Настройки Yandex Cloud для YandexGPT и Vision
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

# Справочник стран
COUNTRIES = {
    "korea": "🇰🇷 Корея",
    "russia": "🇷🇺 Россия",
    "kazakhstan": "🇰🇿 Казахстан",
}

# Категории товаров
CATEGORIES = [
    "Крема",
    "Патчи",
    "Маски",
    "Средства для умывания",
    "БАДы",
    "Сыворотки",
    "Спрей",
    "Разное",
]

# Проверка обязательных переменных
if not TOKEN:
    raise ValueError("❌ Не задан BOT_TOKEN в файле .env")
if not YANDEX_API_KEY:
    raise ValueError("❌ Не задан YANDEX_API_KEY в файле .env")
if not YANDEX_FOLDER_ID:
    raise ValueError("❌ Не задан YANDEX_FOLDER_ID в файле .env")