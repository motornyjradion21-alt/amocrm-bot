from flask import Flask, request
import requests
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)

BOT_TOKEN = "8401828649:AAEiE0s3Otw7ykEkhAw7H_QgIxq3m-5mnsg"
CHAT_ID = "-1003027845340"
MY_ID = "1488994613"
FIELD_MESSENGER_ID = "1355181"

pending_contacts = {}
pending_leads = {}
lock = threading.Lock()

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

def try_match_and_send():
    with lock:
        if not pending_contacts or not pending_leads:
            return
        contact_key = max(pending_contacts.keys())
        contact = pending_contacts.pop(contact_key)
        lead_key = max(pending_leads.keys())
        lead = pending_leads.pop(lead_key)

    send_telegram(
        f"<b>{lead['form_name']}</b>\n"
        f"{cyprus_time()}\n\n"
        f"{contact['name']}\n"
        f"{contact['phone']}\n"
        f"{contact['email']}\n"
        f"{contact['messenger']}"
    )

@app.route("/webhook", methods=["POST"])
def webhook():
    form = request.form.to_dict(flat=False)

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
                tags.append(tag)
                ti += 1

            if any("facebook" in t.lower() for t in tags):
                lead_name = (form.get(f"{p}[name]") or ["Новая заявка"])[0]
                with lock:
                    pending_leads[time.time()] = {"form_name": lead_name or "Новая заявка"}
                threading.Timer(2.0, try_match_and_send).start()

            idx += 1

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

            with lock:
                pending_contacts[time.time()] = {
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "messenger": messenger
                }
            threading.Timer(2.0, try_match_and_send).start()
            idx += 1

    return "OK", 200

@app.route("/", methods=["GET"])
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
