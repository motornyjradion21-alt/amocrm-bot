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
    data = request.json

    if not data or "leads" not in data:
        return jsonify({"ok": True})

    for lead in data["leads"].get("add", []):
        tags = [t.get("name", "").lower() for t in lead.get("tags", [])]

        # Фильтр: только теги содержащие facebook
        if not any("facebook" in tag for tag in tags):
            continue

        fields = {f["field_name"]: f.get("values", [{}])[0].get("value", "")
                  for f in lead.get("custom_fields_values", [])}

        name = fields.get("Имя", "—")
        phone = fields.get("Телефон", "—")
        email = fields.get("Email", "—")
        messenger = fields.get("Мессенджер", "—")
        form_name = fields.get("Название формы", lead.get("name", "—"))
        dt = datetime.fromtimestamp(lead.get("created_at", 0)).strftime("%d.%m.%Y, %H:%M")

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