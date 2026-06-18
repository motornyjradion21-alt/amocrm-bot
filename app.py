from flask import Flask, request
import requests
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = "8401828649:AAEiE0s3Otw7ykEkhAw7H_QgIxq3m-5mnsg"
CHAT_ID = "-1003027845340"
DEBUG_ID = "1488994613"
FIELD_MESSENGER_ID = "1355181"

def send_telegram(text, chat_id=None):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
        "chat_id": chat_id or CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    form = request.form.to_dict(flat=False)
    send_telegram(str(form)[:1000], DEBUG_ID)

    # Обработка сделок
    for action in ("add", "update"):
        idx = 0
        while True:
            p = f"leads[{action}][{idx}]"
            lead_id = (form.get(f"{p}[id]") or [None])[0]
            if not lead_id:
                break

            tags = []
            ti = 0
            while True:
                tag = (form.get(f"{p}[tags][{ti}][name]") or [None])[0]
                if not tag:
                    break
                tags.append(tag.lower())
                ti += 1

            if not any("facebook" in t for t in tags):
                idx += 1
                continue

            name = (form.get(f"{p}[contact_name]") or ["—"])[0]
            form_name = (form.get(f"{p}[name]") or ["—"])[0]
            created_at = (form.get(f"{p}[date_create]") or [0])[0]

            try:
                dt = datetime.fromtimestamp(int(created_at)).strftime("%d.%m.%Y, %H:%M")
            except:
                dt = datetime.now().strftime("%d.%m.%Y, %H:%M")

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
                f"<b>Princess star (Кипр)</b>\n"
                f"{dt}\n\n"
                f"{name}\n"
                f"{phone}\n"
                f"{email}\n"
                f"{messenger}\n\n"
                f"<i>{form_name}</i>"
            )
            idx += 1

    # Обработка контактов
    for action in ("add", "update"):
        idx = 0
        while True:
            p = f"contacts[{action}][{idx}]"
            contact_id = (form.get(f"{p}[id]") or [None])[0]
            if not contact_id:
                break

            name = (form.get(f"{p}[name]") or ["—"])[0]
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

            dt = datetime.now().strftime("%d.%m.%Y, %H:%M")

            send_telegram(
                f"<b>Princess star (Кипр)</b>\n"
                f"{dt}\n\n"
                f"{name}\n"
                f"{phone}\n"
                f"{email}\n"
                f"{messenger}\n\n"
                f"<i>Новый контакт</i>"
            )
            idx += 1

    return "OK", 200

@app.route("/", methods=["GET"])
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
