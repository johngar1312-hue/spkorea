import re
import logging
import json
import aiohttp
import base64
import os
from config import YANDEX_API_KEY, YANDEX_FOLDER_ID

logger = logging.getLogger(__name__)


def is_gift_set(product_name: str, volume: str) -> bool:
    korean_set_keywords = ["기획세트", "세트", "보세트", "선물세트", "gift set", "collection", "kit", "deluxe", "refill"]
    return any(keyword in product_name.lower() for keyword in korean_set_keywords) or "+" in volume


async def detect_text_on_image(image_path: str) -> str:
    print(f"🔍 [DEBUG] Проверяем путь: {image_path}")
    if not os.path.exists(image_path):
        print(f"❌ [DEBUG] Файл не найден: {image_path}")
        logger.error(f"❌ Файл не найден: {image_path}")
        return ""

    file_size = os.path.getsize(image_path)
    print(f"✅ [DEBUG] Файл найден, размер: {file_size} байт")
    if file_size == 0:
        print("❌ [DEBUG] Файл пуст")
        return ""

    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
        if not image_data:
            print("❌ [DEBUG] Данные изображения пусты")
            return ""
        encoded_image = base64.b64encode(image_data).decode("utf-8")
        if len(encoded_image) < 100:
            print("⚠️ [DEBUG] Подозрительно короткий base64")
            return ""
    except Exception as e:
        print(f"❌ [DEBUG] Ошибка при чтении: {e}")
        return ""

    headers = {"Authorization": f"Api-Key {YANDEX_API_KEY}"}
    url = "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze"

    payload = {
        "folderId": YANDEX_FOLDER_ID,
        "analyze_specs": [
            {
                "content": encoded_image,
                "mimeType": "image/jpeg",
                "features": [
                    {
                        "type": "TEXT_DETECTION",
                        "textDetectionConfig": {"languageCodes": ["ko", "en"]}
                    }
                ]
            }
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                print(f"📡 [DEBUG] Статус ответа: {resp.status}")
                if resp.status != 200:
                    text = await resp.text()
                    print(f"❌ [DEBUG] Ошибка: {text}")
                    logger.error(f"❌ Yandex Vision: ошибка {resp.status}")
                    return ""

                result = await resp.json()
                print(f"✅ [DEBUG] Успешный ответ")

                try:
                    text = extract_text_from_detection(result)
                    logger.info(f"✅ Yandex Vision: извлечён текст:\n{text}")
                    return text
                except Exception as e:
                    logger.error(f"❌ Ошибка при извлечении текста: {e}")
                    return ""
    except Exception as e:
        logger.error(f"❌ Ошибка при обращении к Yandex Vision: {e}")
        return ""


def extract_text_from_detection(result: dict) -> str:
    lines = []
    try:
        pages = result["results"][0]["results"][0]["textDetection"]["pages"]
        for page in pages:
            for block in page.get("blocks", []):
                for line in block.get("lines", []):
                    words = [word.get("text", "") for word in line.get("words", [])]
                    line_text = " ".join(words).strip()
                    if line_text:
                        lines.append(line_text)
    except Exception as e:
        logger.error(f"❌ Ошибка при извлечении текста: {e}")
    return "\n".join(lines)


def preprocess_text(text: str) -> str:
    corrections = {
        "I": "1", "l": "1", "O": "0", "°": "", "•": "", "%!": "", "!": "",
        "원%": "원", "원!": "원", "ml |": "ml", "ml I": "ml", "ml1": "ml",
    }
    for old, new in corrections.items():
        text = text.replace(old, new)
    return text.strip()


def extract_products_from_raw_lines(lines: list) -> list:
    products = []
    current = {}
    price_pattern = r'(\d{3,}[,\d]*)\s*원'
    volume_pattern = r'(\d+ml|\d+g|\d+\s*ml|\d+\s*g)'

    product_keywords = ["크림", "앰플", "세럼", "로션", "수분크림", "에센스", "앰풀", "스킨케어"]

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if any(kw in line for kw in product_keywords):
            if current.get("product") and current.get("price_krw"):
                products.append(current)
            refill = "(리필)" in line or "refill" in line.lower()
            clean_name = line.replace("(리필)", "").replace("Refill", "").strip()
            current = {
                "brand": "Amore Pacific",
                "product": clean_name,
                "refill": refill,
                "price_krw": None,
                "volume": None
            }

        if not current.get("volume"):
            vol_match = re.search(volume_pattern, line)
            if vol_match:
                current["volume"] = vol_match.group(1).strip()

        if not current.get("price_krw"):
            price_match = re.search(price_pattern, line)
            if price_match:
                price_str = price_match.group(1).replace(",", "").strip()
                try:
                    price = int(price_str)
                    if 5000 <= price <= 1_500_000:
                        current["price_krw"] = price
                except:
                    pass

    if current.get("product") and current.get("price_krw"):
        products.append(current)
    return products


async def extract_product_data_with_gpt(text: str) -> list:
    headers = {"Authorization": f"Api-Key {YANDEX_API_KEY}", "Content-Type": "application/json"}

    prompt = """
Ты — эксперт по корейским косметическим каталогам.
Проанализируй текст и выдели **все уникальные товары** с ценой.
Включай:
- Основные продукты
- Рефиллы (refill, 리필)
- Наборы

Каждый товар:
- Бренд (Amore Pacific, если не указан)
- Полное название
- Объём (если есть)
- Цена в KRW (только число)
- Признак "refill": true, если это рефилл

Формат (массив JSON):
[
  {
    "brand": "Amore Pacific",
    "product": "Jinsul Cream",
    "volume": "60ml",
    "price_krw": 520000,
    "refill": false
  }
]
"""

    payload = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {"temperature": 0.3, "maxTokens": 1000},
        "messages": [
            {"role": "system", "text": prompt},
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
                if resp.status != 200:
                    logger.error(f"❌ GPT ошибка: {resp.status}")
                    return []

                result = await resp.json()
                content = result["result"]["alternatives"][0]["message"]["text"].strip()
                start, end = content.find('['), content.rfind(']') + 1
                if start == -1:
                    logger.error("❌ JSON не найден")
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    return extract_products_from_raw_lines(lines)

                json_text = content[start:end]
                data = json.loads(json_text)
                filtered_data = []
                for item in data:
                    if "price_krw" in item:
                        try:
                            price = int(str(item["price_krw"]).replace(",", "").strip())
                            if 5000 <= price <= 1_500_000:
                                item["price_krw"] = price
                                # Генерируем артикул ЛИШЬ здесь — как строку
                                item["article"] = f"AP-{len(filtered_data) + 100:03d}"
                                filtered_data.append(item)
                        except:
                            continue
                return filtered_data
    except Exception as e:
        logger.error(f"❌ Ошибка в GPT: {e}")
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return extract_products_from_raw_lines(lines)


async def parse_catalog_with_tesseract(image_path: str) -> list:
    try:
        raw_text = await detect_text_on_image(image_path)
        if not raw_text:
            return []

        clean_text = preprocess_text(raw_text)
        products = await extract_product_data_with_gpt(clean_text)
        logger.info(f"✅ Извлечено: {len(products)} товаров")
        return products
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return []