import os
import datetime
from database import Session
from models import Product
from jinja2 import Environment, FileSystemLoader

# Пути
BOT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BOT_DIR, "templates")
OUTPUT_DIR = os.path.join(BOT_DIR, "output")

# Гарантируем существование папок
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_html_catalog():
    """
    Генерирует HTML-каталог с карточками товаров и кнопками "Добавить в корзину"
    Каждая кнопка ведёт в бота через deep link: t.me/koreazakupkabot?start=product_{article}
    """
    session = Session()
    products = session.query(Product).all()
    session.close()

    if not products:
        raise ValueError("❌ В базе нет товаров. Нельзя сгенерировать каталог.")

    # Группировка по брендам
    grouped = {}
    for p in products:
        name = p.name_en or p.name or ""
        if "Sulwhasoo" in name:
            brand = "Sulwhasoo"
        elif "Amore Pacific" in name:
            brand = "Amore Pacific"
        elif "Innisfree" in name:
            brand = "Innisfree"
        elif "Laneige" in name:
            brand = "Laneige"
        else:
            brand = "Другие бренды"
        grouped.setdefault(brand, []).append(p)

    # Загрузка шаблона
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("catalog.html")

    # Рендер
    html_out = template.render(
        grouped_products=grouped,
        bot_username="koreazakupkabot",  # ✅ Обновлено: ваш username бота
        date=datetime.datetime.now().strftime("%d.%m.%Y")
    )

    # Сохранение
    filepath = os.path.join(OUTPUT_DIR, "catalog.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_out)

    return filepath