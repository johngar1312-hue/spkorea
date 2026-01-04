import pandas as pd
import os
from typing import Dict

BASE_DATA_FILE = "data/base.xlsx"

def load_product_base() -> Dict[str, dict]:
    if not os.path.exists(BASE_DATA_FILE):
        print(f"[INFO] Файл base.xlsx не найден: {BASE_DATA_FILE}")
        return {}

    try:
        df = pd.read_excel(BASE_DATA_FILE)
        if 'name' not in df.columns:
            print(f"[ERROR] В base.xlsx нет столбца 'name'")
            return {}

        df['name'] = df['name'].str.strip().str.lower()
        base = {}
        for _, row in df.iterrows():
            name = row['name']
            base[name] = {
                'description': str(row.get('description', '')) if not pd.isna(row.get('description')) else '',
                'image_url': str(row.get('image_url', '')) if not pd.isna(row.get('image_url')) else '',
            }
        return base
    except Exception as e:
        print(f"[ERROR] Ошибка загрузки base.xlsx: {e}")
        return {}

def find_product_data(name: str) -> dict:
    base = load_product_base()
    return base.get(name.strip().lower(), {'description': '', 'image_url': ''})