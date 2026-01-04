from database import engine, Base
from models import User, Product, Order

print("🔄 Создаём таблицы в базе данных...")

# Удаляем старые таблицы (если нужно)
Base.metadata.drop_all(engine)

# Создаём новые
Base.metadata.create_all(engine)

print("✅ Таблицы успешно созданы!")
