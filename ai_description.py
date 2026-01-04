import logging
import json
import aiohttp
from config import YANDEX_API_KEY, YANDEX_FOLDER_ID

logger = logging.getLogger(__name__)


async def translate_korean_to_english(text: str) -> str:
    """
    Переводит корейский текст на английский с помощью YandexGPT
    """
    if not text.strip():
        return text

    headers = {"Authorization": f"Api-Key {YANDEX_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {"temperature": 0.3, "maxTokens": 500},
        "messages": [
            {"role": "system", "text": "Ты — профессиональный переводчик с корейского на английский. Переведи точно, без пояснений."},
            {"role": "user", "text": text}
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                headers=headers,
                json=payload
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    translation = result["result"]["alternatives"][0]["message"]["text"].strip()
                    if translation.startswith('"') and translation.endswith('"'):
                        translation = translation[1:-1]
                    return translation
                else:
                    logger.error(f"❌ Ошибка перевода: {resp.status}")
                    return text
    except Exception as e:
        logger.error(f"❌ Исключение при переводе: {e}")
        return text


async def generate_description_yandex(brand: str, product: str, volume: str = "") -> str:
    """
    Генерирует подробное, продающее описание товара с акцентом на действии, составе и эффекте.
    Упаковка — кратко, 1–2 предложения.
    """
    headers = {"Authorization": f"Api-Key {YANDEX_API_KEY}", "Content-Type": "application/json"}

    full_name = f"{brand} {product}".strip()
    if volume:
        full_name += f" {volume}"

    prompt = f"""
Ты — топовый копирайтер премиального корейского бренда. Напиши яркое, эмоциональное, продающее описание для:
{full_name}

📌 Цель: читатель должен захотеть купить, потому что ПОНЯЛ, ЧТО ЭТО РАБОТАЕТ.

👉 Структура:
1. 💫 **Вступление с эффектом**:
   - Какой результат даёт продукт? (сияние, упругость, сияющий финиш и т.д.)
   - Какие проблемы решает? (морщинки, тусклость, обезвоженность)

2. 🌿 **Ключевые ингредиенты и технологии**:
   - Какие активные компоненты? (гиалуроновая кислота, ниацинамид, пептиды, центелла азиатская, аденозин, экстракт слизи улитки и т.д.)
   - Есть ли фирменный комплекс бренда? (например, "GinsenCell" у Sulwhasoo, "Cica" у Dr.Jart+)
   - Как они работают? (например: "Ниацинамид — осветляет пигментные пятна", "Гиалурон — удерживает влагу")

3. ✨ **Ощущение и текстура**:
   - Лёгкий гель, насыщенный крем, шелковая сыворотка?
   - Как ведёт себя на коже? (впитывается мгновенно, не липнет, не оставляет плёнки)

4. 📦 **Упаковка**:
   - Только 1–2 предложения: цвет, стиль, практичность. Не больше.

5. 💬 **Завершение с вовлечением**:
   - Призыв к ощущению: "Представьте утро после первого применения…"
   - Эмодзи: 🌸✨💫💎🤍💗

📌 Формат: 3–4 абзаца, на русском, с переносами строк, живым языком.
📌 Не пиши: "фото недоступно", "цена", "закажите сейчас"
"""

    payload = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {
            "temperature": 0.7,
            "maxTokens": 2000
        },
        "messages": [
            {"role": "system", "text": "Ты — эксперт по корейской косметике. Описание должно вызывать желание попробовать."},
            {"role": "user", "text": prompt}
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                headers=headers,
                json=payload
            ) as resp:
                if resp.status != 200:
                    logger.error(f"❌ Ошибка YandexGPT: {resp.status}")
                    return "Премиальный корейский уход. Работает с первого применения. 🌸✨"

                result = await resp.json()
                description = result["result"]["alternatives"][0]["message"]["text"].strip()
                description = "\n".join(line.strip() for line in description.splitlines() if line.strip())

                logger.info(f"✅ Описание сгенерировано для: {full_name}")
                return description

    except Exception as e:
        logger.error(f"❌ Ошибка при генерации описания: {e}")
        return "Эффективный корейский уход. Проверено в Сеуле. 🌟💎"