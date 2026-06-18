from flask import Flask, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = "8401828649:AAEiE0s3Otw7ykEkhAw7H_QgIxq3m-5mnsg"
CHAT_ID = "-1003027845340"
DEBUG_ID = "1488994613"

def send_telegram(message, chat_id=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id or CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    form = request.form.to_dict(flat=False)
    
    # Дебаг — шлём сырые данные себе
    send_telegram(f"RAW:\n{str(form)[:1000]}", DEBUG_ID)

    for action in ("add", "update"):
        idx = 0
        while True:
            prefix = f"leads[{action}][{idx}]"
            lead_id = form.get(f"{prefix}[id]", [None])[0]
            if not lead_id:
                break

            # Теги
            tags = []
            tag_idx = 0
            while True:
                tag = form.get(f"{prefix}[tags][{tag_idx}][name]", [None])[0]
                if not tag:
                    break
                tags.append(tag.lower())
                tag_idx += 1

            # Фильтр Facebook
            if not any("facebook" in t for t in tags):
                idx += 1
                continue

            # Имя контакта
            name = form.get(f"{prefix}[contact_name]", ["—"])[0]

            # Кастомные поля
            phone, email, messenger = "—", "—", "—"
            field_idx = 0
            while True:
                fid = form.get(f"{prefix}[custom_fields][{field_idx}][id]", [None])[0]
                if not fid:
                    break
                val = form.get(f"{prefix}[custom_fields][{field_idx}][values][0][value]", ["—"])[0]
                code = form.get(f"{prefix}[custom_fields][{field_idx}][code]", [""])[0]
                fname = form.get(f"{prefix}[custom_fields][{field_idx}][name]", [""])[0].lower()
                
                if code == "PHONE" or "телефон" in fname or "phone" in fname:
                    phone = val
                elif code == "EMAIL" or "email" in fname:
                    email = val
                elif "мессенджер" in fname or "messenger" in fname:
                    messenger = val
                
                field_idx += 1

            form_name = next((t for t in tags if "facebook" not in t), "—")
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
            idx += 1

    return "OK", 200

@app.route("/", methods=["GET"])
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
