import pandas as pd
from database import Session
from models import Order, Product, User
import os
from datetime import datetime


def generate_orders_excel():
    """
    Генерирует Excel-файл с заказами для админа
    Сгруппировано по ПВЗ, с итогами
    """
    session = Session()

    # Запрос: все подтверждённые заказы
    query = """
    SELECT
        u.name as Участник,
        u.pickup_address as ПВЗ,
        u.delivery_method as Доставка,
        p.article as Артикул,
        p.name_en as Товар,
        o.quantity as Кол,
        p.price as Цена_₽,
        o.quantity * p.price as Сумма_₽
    FROM orders o
    JOIN users u ON o.user_id = u.id
    JOIN products p ON o.product_id = p.id
    WHERE o.status = 'confirmed'
    ORDER BY u.pickup_address, u.name, p.name_en
    """
    df = pd.read_sql_query(query, session.bind)

    # Итоги по ПВЗ
    summary = df.groupby('ПВЗ').agg({
        'Сумма_₽': 'sum',
        'Участник': 'count'
    }).round(0).astype(int)
    summary = summary.rename(columns={'Сумма_₽': 'Итого ₽', 'Участник': 'Заказов'})

    # Сохранение в Excel
    filename = f"orders_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    filepath = os.path.join("orders", filename)
    os.makedirs("orders", exist_ok=True)

    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Заказы', index=False)
        summary.to_excel(writer, sheet_name='Итоги по ПВЗ')

        # Форматирование
        workbook = writer.book
        worksheet = writer.sheets['Заказы']

        # Автоширина
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    session.close()
    return filepath