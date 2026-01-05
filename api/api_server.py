from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

# 🔹 Убедимся, что папка sessions рядом с api_server.py
SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

@app.route('/api/save', methods=['POST'])
def save_session():
    data = request.json
    session_id = data.get("session_id")
    products = data.get("products", [])

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"✅ Сессия сохранена: {filepath}")
        return jsonify({"status": "saved"}), 200
    except Exception as e:
        print(f"❌ Ошибка записи: {e}")
        return jsonify({"error": "failed to save"}), 500

@app.route('/api/products', methods=['GET'])
def get_products():
    session_id = request.args.get("session")
    if not session_id:
        return jsonify([])

    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if not os.path.exists(filepath):
        print(f"❌ Файл не найден: {filepath}")
        return jsonify([])

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"✅ Данные загружены: {len(data)} товаров")
        return jsonify(data)
    except Exception as e:
        print(f"❌ Ошибка чтения: {e}")
        return jsonify([])

@app.route('/')
def index():
    return "Mini App API is running."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
