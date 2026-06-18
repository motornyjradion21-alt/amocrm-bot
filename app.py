from flask import Flask, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = "8401828649:AAEiE0s3Otw7ykEkhAw7H_QgIxq3m-5mnsg"
CHAT_ID = "-1003027845340"
DEBUG_ID = "1488994613"
AMO_DOMAIN = "eurozats.amocrm.ru"
AMO_API_KEY = "svb7twrPkYMmu8Mi28segyzq2sexZRkBu6FzewDUu8WcZXtLm76UuCirxEhUR6OL"

def send_telegram(message, chat_id=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id or CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    })

def get_contact(contact_id):
    url = f"https://{AMO_DOMAIN}/api/v4/contacts/{contact_id}"
    headers = {"Authorization": f"Bearer {AMO_API_KEY}"}
    r = requests.get(url, headers=headers)
    send_telegram(f"Contact API: {r.status_code}\n{r.text[:300]}", DEBUG_ID)
    if r.status_code == 200:
        return r.json()
    return None

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.form.to_dict(flat=False)
    if not data:
        return jsonify({"ok": True})

    tags = []
    for key, value in data.items():
        if "tags" in key.lower():
            tags.extend([v.lower() for v in value])

    if not any("facebook" in tag for tag in tags):
        return jsonify({"ok": True})

    contact_id = None
    for key, value in data.items():
        if "contacts" in key.lower() and "id" in key.lower():
            contact_id = value[0]
            break

    send_telegram(f"Debug: contact_id={contact_id}\ntags={tags}", DEBUG_ID)

    name, phone, email, messenger = "—", "—", "—", "—"

    if contact_id:
        contact = get_contact(contact_id)
        if contact:
            name = contact.get("name", "—")
            for field in contact.get("custom_fields_values", []) or []:
                fname = field.get("field_name", "").lower()
                fvalue = field.get("values", [{}])[0].get("value", "—")
                if "phone" in fname or "телефон" in fname:
                    phone = fvalue
                elif "email" in fname:
                    email = fvalue
                elif "messenger" in fname or "мессенджер" in fname:
                    messenger = fvalue

    form_name = next((t for t in tags if t != "facebook"), "—")
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
