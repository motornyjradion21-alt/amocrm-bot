from flask import Flask, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = "8401828649:AAEiE0s3Otw7ykEkhAw7H_QgIxq3m-5mnsg"
CHAT_ID = "-1003027845340"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    # AmoCRM шлёт form-urlencoded
    data = request.form.to_dict(flat=False)
    
    if not data:
        return jsonify({"ok": True})

    # Логируем для отладки
    print("Received data:", data)

    # Достаём теги
    tags = []
    for key, value in data.items():
        if "tags" in key.lower():
            tags.extend([v.lower() for v in value])

    # Фильтр Facebook
    if not any("facebook" in tag for tag in tags):
        return jsonify({"ok": True})

    # Достаём поля
    def get_field(prefix):
        for key, value in data.items():
            if prefix.lower() in key.lower():
                return value[0] if value else "—"
        return "—"

    name = get_field("name")
    phone = get_field("phone")
    email = get_field("email")
    messenger = get_field("messenger")
    form_name = get_field("form")
    dt = datetime.now().strftime("%d.%m.%Y, %H:%M")

    message = (
        f"<b>Princess star (Кипр)</b>\n"
        f"{dt}\n\n"
        f"{name}\n"
        f"{phone}\n"
        f"{email}\n"
        f"{messenger}\n\n"
        f"<i>{form_name}</i>"
    )

    send_telegram(message)
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
