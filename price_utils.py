import math
from config import EXCHANGE_RATE


def round_up_to_10(price: float) -> int:
    return math.ceil(price / 10) * 10


def convert_krw_to_rub_with_discount_and_markup(
    price_krw: float,
    is_korean_catalog: bool = True
) -> int:
    """
    Конвертирует KRW → RUB с учётом:
    - is_korean_catalog: скидка 55% (опт)
    - ВСЕГДА: наша наценка +22%
    - округление до 10
    """
    # Шаг 1: Применяем скидку 55% только если это корейский каталог
    if is_korean_catalog:
        price_after_wholesale = price_krw * 0.45  # -55%
    else:
        price_after_wholesale = price_krw  # цена уже в KRW без скидки

    # Шаг 2: Конвертируем в RUB
    price_rub = price_after_wholesale * EXCHANGE_RATE

    # Шаг 3: ВСЕГДА добавляем наценку +22%
    final_price_rub = price_rub * 1.22

    # Шаг 4: Округляем вверх до 10
    return round_up_to_10(final_price_rub)