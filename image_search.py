import asyncio
import json
import os
from typing import Optional
import requests
from ai_description import translate_korean_to_english

# Кэш для URL изображений
CACHE_FILE = "data/image_cache.json"
os.makedirs("data", exist_ok=True)

# Загружаем кэш
_image_cache = {}
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            _image_cache = json.load(f)
    except Exception as e:
        print(f"[WARNING] Не удалось загрузить кэш: {e}")


def _save_cache():
    """Сохраняет кэш в файл"""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(_image_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] Не удалось сохранить кэш: {e}")


def is_clean_url(url: str) -> bool:
    """Фильтрует рекламные, промо, неподходящие URL"""
    url_lower = url.lower()

    # Блокируем рекламные/непрямые домены
    bad_domains = [
        "stories.amorepacific.com",
        "cdn-design.amorepacific.com",
        "blog.", "naver.com", "tistory.com", "youtube.com",
        "us.laneige.com", "us.sulwhasoo.com", "us.amorepacific.com",
        "editorial.", "campaign.", "promotion.",
        "community.sephora.com",
        "incidecoder.com",
        "bestkoreanskincare.kr"
    ]
    if any(domain in url_lower for domain in bad_domains):
        return False

    # Блокируем по шаблонам в URL
    bad_patterns = [
        "blog", "post", "story", "event", "promotion", "campaign",
        "banner", "ad", "advertisement", "youtube", "review",
        "view_", "list_", "alt_", "holiday", "giftguide",
        "lookbook", "popup", "magazine", "story",
        "banner", "promo", "flashsale", "freeshipping",
        "serverpage", "?v=v2", "image-id"  # Для community.sephora.com
    ]
    if any(pattern in url_lower for pattern in bad_patterns):
        return False

    # Разрешаем только нужные домены и корейские версии
    allowed_domains = [
        "oliveyoung.com", "coupang.com", "gmarket.co.kr", "11st.co.kr"
    ]
    if any(domain in url_lower for domain in allowed_domains):
        return True

    # Или корейские версии брендов
    brand_kr_patterns = [
        "amorepacific.com/kr/", "sulwhasoo.com/kr/",
        "innisfree.com/kr/", "laneige.com/kr/",
        "hera.com/kr/", "mamonde.com/kr/"
    ]
    if any(pattern in url_lower for pattern in brand_kr_patterns):
        return True

    return False


async def is_direct_image_url(url: str) -> bool:
    """Проверяет, что URL ведёт напрямую на изображение (не на HTML)"""
    try:
        response = requests.head(url, timeout=3, allow_redirects=True)
        content_type = response.headers.get("Content-Type", "")
        return content_type.startswith("image/")
    except:
        return False


def is_high_quality_image(url: str) -> bool:
    """Проверяет, что изображение не слишком маленькое"""
    try:
        response = requests.head(url, timeout=3)
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) < 30_000:
            return False
        return True
    except:
        return False


async def find_image_url(brand: str, product: str, volume: str = "") -> Optional[str]:
    """
    Ищет URL изображения по бренду и продукту.
    Приоритет: кэш → DDG с фильтрами → общий поиск
    """
    original_query = f"{brand} {product} {volume}".strip()
    if not original_query:
        return None

    # Проверяем кэш
    key = original_query.lower().strip()
    if key in _image_cache:
        print(f"[DEBUG] Найдено в кэше: {key} → {_image_cache[key]}")
        return _image_cache[key]

    # Переводим на английский
    translated_product = await translate_korean_to_english(product)
    full_query_en = f"{brand} {translated_product} {volume}".strip()

    # Пробуем поиск
    for query in [full_query_en, original_query]:
        result = await _search_with_filters(query)
        if result:
            # Дополнительная проверка: прямая ссылка на изображение
            if await is_direct_image_url(result):
                _image_cache[key] = result
                _save_cache()
                print(f"[DEBUG] Сохранено в кэш: {key} → {result}")
                return result
            else:
                print(f"[DEBUG] Пропущено (не прямое фото): {result}")

    return None


async def _search_with_filters(query: str) -> Optional[str]:
    """Выполняет поиск с фильтрацией по качеству и источникам"""
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            official_sites = [
                "oliveyoung.com", "coupang.com", "gmarket.co.kr", "11st.co.kr"
            ]
            # Добавляем корейские версии брендов
            brand_sites = [
                "amorepacific.com/kr", "sulwhasoo.com/kr",
                "innisfree.com/kr", "laneige.com/kr",
                "hera.com/kr", "mamonde.com/kr"
            ]
            all_sites = official_sites + brand_sites
            site_filter = " OR ".join([f"site:{site}" for site in all_sites])

            search_queries = [
                f"{query} official product packaging front view high resolution {site_filter}",
                f"{query} 정품 제품 포장 전면 사진 고화질 {site_filter}",
                f"{query} product photo front main image {site_filter}",
                f"{query} gift set product packaging {site_filter}",
                f"{query} 제품 사진 공식 {site_filter}"
            ]

            for search_query in search_queries:
                try:
                    print(f"[DEBUG] Поиск: {search_query}")
                    results = ddgs.images(
                        query=search_query,
                        region="kr-kr",
                        safesearch="off",
                        size="Large",
                        type_image="photo",
                        max_results=10
                    )

                    for r in results:
                        img_url = r.get("image")
                        if not img_url:
                            continue

                        print(f"[DEBUG] Найдено изображение: {img_url}")

                        if not is_clean_url(img_url):
                            print(f"[DEBUG] Пропущено (плохой URL): {img_url}")
                            continue

                        if not is_high_quality_image(img_url):
                            print(f"[DEBUG] Пропущено (низкое качество): {img_url}")
                            continue

                        # Проверяем, ведёт ли ссылка напрямую на изображение
                        if not await is_direct_image_url(img_url):
                            print(f"[DEBUG] Пропущено (не прямое изображение): {img_url}")
                            continue

                        title = r.get("title", "").lower()
                        if any(word in title for word in ["front", "main", "정품", "gift", "set", "product", "packaging"]):
                            print(f"[DEBUG] ✅ Выбрано по приоритету: {img_url}")
                            return img_url

                    # Если не нашли с приоритетом — возвращаем первое подходящее
                    for r in results:
                        img_url = r.get("image")
                        if not img_url:
                            continue
                        if is_clean_url(img_url) and is_high_quality_image(img_url) and await is_direct_image_url(img_url):
                            print(f"[DEBUG] ✅ Возвращаем первое подходящее: {img_url}")
                            return img_url

                except Exception as e:
                    print(f"[INFO] Поиск не удался для: {search_query} | {e}")
                    continue

    except ImportError:
        print("[ERROR] Установите: pip install duckduckgo-search")
    except Exception as e:
        print(f"[ERROR] Ошибка в поиске: {e}")

    return None