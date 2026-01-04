import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from config import BOT_TOKEN, ADMIN_IDS
from database import Session, init_db
from models import Product, User
from vision_parser import parse_catalog_with_tesseract
from ai_description import generate_description_yandex
from price_utils import convert_krw_to_rub_with_discount_and_markup
import os
import json
import base64

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

user_cart = {}
user_states = {}
UPLOAD_STATE = {}

PICKUP_OPTIONS = ["СДЭК", "Почта РФ", "Ozon", "AliExpress"]
PICKUP_ADDRESSES = {
    "СДЭК": "г. Москва, ул. Ленина, д. 1",
    "Почта РФ": "г. Москва, ул. Победы, д. 10",
    "Ozon": "г. Москва, склад Ozon, ПВЗ №123",
    "AliExpress": "г. Москва, терминал AE, зона B"
}
IS_COLLECTION_OPEN = True

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = Session()
    user = session.query(User).filter_by(telegram_id=user_id).first()
    session.close()

    # Обработка deep link: добавление товара
    text = update.message.text.strip()
    if " " in text:
        parts = text.split(" ", 1)
        if len(parts) > 1:
            payload = parts[1]
            if payload.startswith("add_"):
                article = payload.split("add_")[-1]
                session = Session()
                product = session.query(Product).filter_by(article=article).first()
                session.close()

                if not product:
                    await update.message.reply_text("❌ Товар не найден.")
                    return

                cart = user_cart.setdefault(user_id, [])
                if article not in [p["article"] for p in cart]:
                    cart.append({"product": product, "quantity": 1, "article": article})
                    await update.message.reply_text(f"✅ *{product.name_en}* добавлен в корзину.", parse_mode="Markdown")
                else:
                    await update.message.reply_text("🛒 Уже в корзине!")
                return

    # Обычный старт
    if user:
        await update.message.reply_text(
            f"👋 С возвращением, {user.name}!\n"
            "Используйте:\n"
            "• /catalog — получить каталог\n"
            "• /cart — посмотреть корзину\n"
            "• /upload_photo — загрузить фото"
        )
    else:
        await update.message.reply_text("📝 Введите ваше имя для регистрации:")
        user_states[user_id] = "awaiting_name"

# --- ОБРАБОТКА ТЕКСТА ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id in user_states:
        if user_states[user_id] == "awaiting_name":
            session = Session()
            user = User(telegram_id=user_id, name=text)
            session.add(user)
            session.commit()
            session.close()

            keyboard = [[InlineKeyboardButton(option, callback_data=f"delivery_{option}")] for option in PICKUP_OPTIONS]
            await update.message.reply_text("🚚 Выберите способ доставки:", reply_markup=InlineKeyboardMarkup(keyboard))
            user_states[user_id] = "awaiting_delivery"
            return

    if not text.startswith("/"):
        await update.message.reply_text("Используйте команды из меню.")

# --- КНОПКИ ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    await query.answer()
    logger.info(f"Кнопка: {data} от {user_id}")

    if data.startswith("delivery_"):
        method = data.split("_", 1)[1]
        session = Session()
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if user:
            user.delivery_method = method
            user.pickup_address = PICKUP_ADDRESSES[method]
            session.commit()
        session.close()
        await query.edit_message_text(
            f"✅ Способ доставки: *{method}*\n"
            f"📦 Адрес: {PICKUP_ADDRESSES[method]}\n\n"
            "Теперь используйте /catalog — получить каталог",
            parse_mode="Markdown"
        )
        user_states.pop(user_id, None)

    elif data == "generate_catalog":
        if not IS_COLLECTION_OPEN:
            await query.edit_message_text("❌ Закупка приостановлена.")
            return
        try:
            path = "output/catalog.html"
            with open(path, "r", encoding="utf-8") as f:
                await context.bot.send_document(chat_id=user_id, document=f, filename="Каталог.html")
            await context.bot.send_message(user_id, "✅ HTML-каталог отправлен.")
        except Exception as e:
            await context.bot.send_message(user_id, f"❌ Ошибка: {e}")

    elif data.startswith("add_to_cart_"):
        article = data.split("_")[-1]
        session = Session()
        product = session.query(Product).filter_by(article=article).first()
        session.close()

        if not product:
            await query.edit_message_text("❌ Товар не найден.")
            return

        cart = user_cart.setdefault(user_id, [])
        if article not in [p["article"] for p in cart]:
            cart.append({"product": product, "quantity": 1, "article": article})
            await query.edit_message_text(
                f"✅ *{product.name_en}* добавлен в корзину.\nИспользуйте /cart",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("🛒 Уже в корзине!")

# --- ЗАГРУЗКА ФОТО ---
async def upload_photo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Только админ.")
        return

    keyboard = [
        [InlineKeyboardButton("🇰🇷 Корейский каталог (KRW)", callback_data="upload_korean")],
        [InlineKeyboardButton("📊 Excel (RUB)", callback_data="upload_excel")]
    ]
    await update.message.reply_text("📤 Выберите тип файла:", reply_markup=InlineKeyboardMarkup(keyboard))

async def upload_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    await query.answer()

    if data == "upload_korean":
        UPLOAD_STATE[user_id] = "korean_catalog"
        await query.edit_message_text("📸 Пришлите фото корейского каталога.")
    elif data == "upload_excel":
        UPLOAD_STATE[user_id] = "excel_catalog"
        await query.edit_message_text("📸 Пришлите фото Excel-таблицы (цены в RUB).")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Только админ.")
        return
    if user_id not in UPLOAD_STATE:
        await update.message.reply_text("Сначала используйте /upload_photo")
        return

    source_type = UPLOAD_STATE.pop(user_id)
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_path = f"uploads/{file.file_id}.jpg"
    os.makedirs("uploads", exist_ok=True)
    await file.download_to_drive(file_path)

    try:
        products_data = await parse_catalog_with_tesseract(file_path)
        added = 0
        session = Session()

        for item in products_data:
            existing = session.query(Product).filter_by(article=item["article"]).first()
            if existing:
                continue

            if source_type == "excel_catalog":
                price_rub = item["price_krw"]  # Уже в RUB
            else:
                price_rub = convert_krw_to_rub_with_discount_and_markup(
                    item["price_krw"],
                    is_korean_catalog=True
                )

            description = await generate_description_yandex(
                brand=item["brand"],
                product=item["product"],
                volume=item.get("volume", "")
            )

            product = Product()
            product.article = item["article"]
            product.name = item["product"]
            product.name_en = item["product"]
            product.brand = item["brand"]
            product.price = price_rub
            product.description = description
            product.volume = item.get("volume", "")
            product.category = "Крема"
            product.country = "Корея"
            product.in_stock = 10

            session.add(product)
            added += 1

        session.commit()
        session.close()
        await update.message.reply_text(f"✅ Добавлено: {added} товаров")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# --- КОРЗИНА ---
async def cart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cart = user_cart.get(update.effective_user.id, [])
    if not cart:
        await update.message.reply_text("🛒 Ваша корзина пуста.")
        return

    total = sum(item["quantity"] * item["product"].price for item in cart)
    message = "🛒 *Ваша корзина*\n\n"
    for i, item in enumerate(cart, 1):
        p = item["product"]
        qty = item["quantity"]
        message += f"{i}. {p.name_en}\n   {qty} × {p.price:,} ₽ = {(qty * p.price):,} ₽\n"
    message += f"\n*Итого: {total:,} ₽*"

    keyboard = [[InlineKeyboardButton("Очистить корзину", callback_data="clear_cart")]]
    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- MINI APP: /catalog ---
async def send_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    products = session.query(Product).all()
    session.close()

    if not products:
        await update.message.reply_text("❌ В базе нет товаров.")
        return

    data = []
    for p in products:
        data.append({
            "id": p.id,
            "article": p.article,
            "name": p.name_en or p.name,
            "brand": p.brand,
            "volume": p.volume or "",
            "price": p.price,
            "description": p.description or ""
        })

    json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    encoded = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('ascii')

    # Замените на ваш GitHub Pages URL
    url = f"https://johngar1312-hue.github.io/korea-catalog-miniapp?data={encoded}"

    keyboard = [[InlineKeyboardButton("📱 Открыть каталог", web_app=WebAppInfo(url=url))]]
    await update.message.reply_text("📂 Откройте каталог в Mini App:", reply_markup=InlineKeyboardMarkup(keyboard))

# --- АДМИН ---
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    kb = [
        [InlineKeyboardButton("📤 Сгенерировать HTML-каталог", callback_data="generate_catalog")],
        [InlineKeyboardButton("🚫 Закрыть закупку", callback_data="close_collection")]
    ]
    await update.message.reply_text("⚙️ Админ-панель", reply_markup=InlineKeyboardMarkup(kb))

async def close_collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global IS_COLLECTION_OPEN
    query = update.callback_query
    IS_COLLECTION_OPEN = False
    await query.edit_message_text("🛑 Закупка закрыта.")

# --- ЗАПУСК ---
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("catalog", send_catalog))
    app.add_handler(CommandHandler("cart", cart_command))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("upload_photo", upload_photo_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    app.add_handler(CallbackQueryHandler(close_collection, pattern="^close_collection$"))
    app.add_handler(CallbackQueryHandler(upload_type_handler, pattern="^upload_"))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("✅ Бот запущен. Mini App активирован.")
    app.run_polling()

if __name__ == "__main__":
    main()