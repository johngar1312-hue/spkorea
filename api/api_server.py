from flask import Flask, jsonify, request
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

SESSIONS_DIR = "/home/ваш-пользователь/korea-bot/sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

SESSION_TTL = timedelta(minutes=30)

def clean_old_sessions():
    now = datetime.now()
    for file in os.listdir(SESSIONS_DIR):
        path = os.path.join(SESSIONS_DIR, file)
        if os.path.getctime(path) < (now - SESSION_TTL).timestamp():
            os.remove(path)

@app.route('/api/save', methods=['POST'])
def save_products():
    data = request.json
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "No session_id"}), 400

    clean_old_sessions()
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data["products"], f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True})

@app.route('/api/products', methods=['GET'])
def get_products():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify([])
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if not os.path.exists(path):
        return jsonify([])
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except:
        return jsonify([])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)