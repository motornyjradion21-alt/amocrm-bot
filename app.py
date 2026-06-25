from flask import Flask, request
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

BOT_TOKEN = "8401828649:AAEiE0s3Otw7ykEkhAw7H_QgIxq3m-5mnsg"
CHAT_ID = "-1003027845340"
MY_ID = "1488994613"
FIELD_MESSENGER_ID = "1355181"

def send_telegram(text):
    for cid in [CHAT_ID, MY_ID]:
        try:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
                "chat_id": cid,
                "text": text,
                "parse_mode": "HTML"
            }, timeout=10)
        except:
            pass

def cyprus_time():
    return (datetime.utcnow() + timedelta(hours=3)).strftime("%d.%m.%Y, %H:%M")

@app.route("/webhook", methods=["POST"])
def webhook():
    form = request.form.to_dict(flat=False)

    # Обрабатываем контакты — шлём сразу
    for action in ("add", "update"):
        idx = 0
        while True:
            p = f"contacts[{action}][{idx}]"
            contact_id = (form.get(f"{p}[id]") or [None])[0]
            if not contact_id:
                break

            name = (form.get(f"{p}[name]") or ["Аноним"])[0]
            phone, email, messenger = "—", "—", "—"

            fi = 0
            while True:
                fid = (form.get(f"{p}[custom_fields][{fi}][id]") or [None])[0]
                if not fid:
                    break
                val = (form.get(f"{p}[custom_fields][{fi}][values][0][value]") or ["—"])[0]
                code = (form.get(f"{p}[custom_fields][{fi}][code]") or [""])[0]

                if code == "PHONE":
                    phone = val
                elif code == "EMAIL":
                    email = val
                elif str(fid) == FIELD_MESSENGER_ID:
                    messenger = val
                fi += 1

            send_telegram(
                f"{cyprus_time()}\n\n"
                f"Имя: {name}\n"
                f"Телефон: {phone}\n"
                f"Email: {email}\n"
                f"Мессенджер: {messenger}"
            )
            idx += 1

    return "OK", 200

@app.route("/", methods=["GET"])
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
