import json
import pandas as pd
import os
from typing import List, Dict

# --- НАСТРОЙКИ ---
INPUT_JSON = "products.json"          # Ваши данные
OUTPUT_BASE = "data/base.xlsx"        # Справочник для автозаполнения
OUTPUT_NEW = "uploads/new_products.xlsx"  # Для загрузки в бота

# Курс: 1 KRW = 0.013 RUB (пример)
EXCHANGE_RATE = 0.013

# Категории по ключевым словам (можно расширить)
CATEGORY_MAP = {
    "сыворотка": "Сыворотки",
    "тоник": "Средства для умывания",
    "крем": "Крема",
    "патчи": "Патчи",
    "маска": "Маски",
    "бад": "БАДы",
}

# --- ФУНКЦИЯ: определение категории ---
def get_category(product_name: str) -> str:
    name_lower = product_name.lower()
    for word, category in CATEGORY_MAP.items():
        if word in name_lower:
            return category
    return "Разное"

# --- ФУНКЦИЯ: очистка и конвертация цены ---
def clean_price_krw(price_str: str) -> int:
    # Убираем "원", пробелы, запятые
    cleaned = price_str.replace("원", "").replace(",", "").replace(" ", "").strip()
    try:
        return int(cleaned)
    except ValueError:
        return 0

def convert_to_rub(krw: int) -> float:
    return round(krw * EXCHANGE_RATE, 2)

# --- ОСНОВНОЙ КОД ---
def main():
    # Создаём папки
    os.makedirs("data", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)

    # Читаем JSON
    if not os.path.exists(INPUT_JSON):
        print(f"[ОШИБКА] Файл {INPUT_JSON} не найден!")
        return

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data: List[Dict] = json.load(f)

    base_data = []
    new_products_data = []

    for item in data:
        brand = item.get("brand", "").strip()
        product = item.get("product", "").strip()
        volume = item.get("volume", "").strip()
        price_krw_str = item.get("price", "").strip()

        # Собираем имя
        if volume:
            name = f"{brand} {product}, {volume}"
        else:
            name = f"{brand} {product}"

        # Цена
        price_krw = clean_price_krw(price_krw_str)
        price_rub = convert_to_rub(price_krw)

        # Категория
        category = get_category(product)

        # --- Для base.xlsx (справочник) ---
        base_data.append({
            "name": name,
            "description": "",  # Вы можете заполнить потом вручную
            "image_url": "",    # Оставить пустым — вы добавите позже
        })

        # --- Для new_products.xlsx (загрузка в бота) ---
        new_products_data.append({
            "name": name,
            "price": price_rub,
            "category": category,
            "country": "Корея",
            "in_stock": False,
        })

    # Сохраняем base.xlsx
    df_base = pd.DataFrame(base_data)
    df_base.to_excel(OUTPUT_BASE, index=False)
    print(f"✅ Справочник сохранён: {OUTPUT_BASE}")

    # Сохраняем new_products.xlsx
    df_new = pd.DataFrame(new_products_data)
    df_new.to_excel(OUTPUT_NEW, index=False)
    print(f"✅ Товары для загрузки: {OUTPUT_NEW}")
    print(f"📦 Всего обработано: {len(data)} товаров")

if __name__ == "__main__":
    main()
