from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = "sqlite:///data/bot.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Session = scoped_session(SessionLocal)


def init_db():
    """Создаёт таблицы, если их нет, и добавляет недостающие колонки"""
    # Создаём таблицы, если не существуют
    Base.metadata.create_all(bind=engine)

    # Проверяем структуру таблицы products
    inspector = inspect(engine)

    if 'products' in inspector.get_table_names():
        existing_columns = {col['name'] for col in inspector.get_columns('products')}

        # Обновляем: in_stock теперь INTEGER
        new_columns = [
            ('image_url', 'VARCHAR(500)', "''"),
            ('in_stock', 'INTEGER', '0'),
            ('category', 'VARCHAR(100)', "'Разное'"),
            ('country', 'VARCHAR(50)', "'Корея'"),
            ('brand', 'VARCHAR(100)', "'Amore Pacific'"),  # ✅ Добавьте
        ]

        with engine.connect() as conn:
            for col_name, col_type, default in new_columns:
                if col_name not in existing_columns:
                    default_clause = f" DEFAULT {default}" if default else ""
                    sql = f"ALTER TABLE products ADD COLUMN {col_name} {col_type}{default_clause};"
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"[INFO] Добавлена колонка: {col_name} в таблицу products")

# ✅ Важно: вызываем init_db() при старте
init_db()
