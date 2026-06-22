from flask import Flask, request, jsonify, redirect
import requests
from datetime import datetime, timedelta
import threading
import time
import json
import os

app = Flask(__name__)

BOT_TOKEN = "8401828649:AAEiE0s3Otw7ykEkhAw7H_QgIxq3m-5mnsg"
CHAT_ID = "-1003027845340"
FIELD_MESSENGER_ID = "1355181"
AMO_DOMAIN = "eurozats.amocrm.ru"
AMO_CLIENT_ID = "d0360f76-edf4-451c-807f-3cb53cd9da86"
AMO_CLIENT_SECRET = "svb7twrPkYMmu8Mi28segyzq2sexZRkBu6FzewDUu8WcZXtLm76UuCirxEhUR6OL"
AMO_REDIRECT_URI = "https://amocrm-bot-production-4773.up.railway.app/oauth/callback"

TOKEN_FILE = "/tmp/tokens.json"

pending_contacts = {}
pending_leads = {}
lock = threading.Lock()

def save_tokens(access_token, refresh_token, expires_in):
    tokens = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": time.time() + expires_in
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f)

def load_tokens():
    try:
        with open(TOKEN_FILE) as f:
            return json.load(f)
    except:
        return None

def get_access_token():
    tokens = load_tokens()
    if not tokens:
        return None
    if time.time() > tokens["expires_at"] - 300:
        return refresh_access_token(tokens["refresh_token"])
    return tokens["access_token"]

def refresh_access_token(refresh_token):
    try:
        r = requests.post(f"https://{AMO_DOMAIN}/oauth2/access_token", json={
            "client_id": AMO_CLIENT_ID,
            "client_secret": AMO_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "redirect_uri": AMO_REDIRECT_URI
        }, timeout=15)
        data = r.json()
        save_tokens(data["access_token"], data["refresh_token"], data["expires_in"])
        return data["access_token"]
    except Exception as e:
        print(f"Refresh error: {e}")
        return None

def send_telegram(text, chat_id=None):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
        "chat_id": chat_id or CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    })

def cyprus_time():
    return (datetime.utcnow() + timedelta(hours=3)).strftime("%d.%m.%Y, %H:%M")

def get_lead_details(lead_id, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        r = requests.get(f"https://{AMO_DOMAIN}/api/v4/leads/{lead_id}?with=contacts,source_id", headers=headers, timeout=10)
        return r.json()
    except:
        return None

def get_contact_details(contact_id, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        r = requests.get(f"https://{AMO_DOMAIN}/api/v4/contacts/{contact_id}", headers=headers, timeout=10)
        return r.json()
    except:
        return None

def get_source_name(source_id, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        r = requests.get(f"https://{AMO_DOMAIN}/ajax/v4/sources?limit=250", headers=headers, timeout=10)
        sources = r.json().get("_embedded", {}).get("sources", [])
        for s in sources:
            if s.get("id") == source_id:
                return s.get("name", "")
    except:
        pass
    return ""

def process_lead_with_api(lead_id, lead_name):
    access_token = get_access_token()
    if not access_token:
        return

    lead = get_lead_details(lead_id, access_token)
    if not lead:
        return

    source_name = ""
    if lead.get("source_id"):
        source_name = get_source_name(lead["source_id"], access_token)

    form_name = source_name or lead_name or "Новая заявка"

    contact_name, phone, email, messenger = "—", "—", "—", "—"
    contacts = lead.get("_embedded", {}).get("contacts", [])
    if contacts:
        contact = get_contact_details(contacts[0]["id"], access_token)
        if contact:
            contact_name = contact.get("name", "—")
            for f in contact.get("custom_fields_values", []) or []:
                code = f.get("field_code", "")
                fname = f.get("field_name", "").lower()
                val = f.get("values", [{}])[0].get("value", "—")
                if code == "PHONE":
                    phone = val
                elif code == "EMAIL":
                    email = val
                elif "мессенджер" in fname or "messenger" in fname:
                    messenger = val

    send_telegram(
        f"<b>{form_name}</b>\n"
        f"{cyprus_time()}\n\n"
        f"{contact_name}\n"
        f"{phone}\n"
        f"{email}\n"
        f"{messenger}"
    )

@app.route("/oauth/callback")
def oauth_callback():
    code = request.args.get("code")
    if not code:
        return "No code", 400
    try:
        r = requests.post(f"https://{AMO_DOMAIN}/oauth2/access_token", json={
            "client_id": AMO_CLIENT_ID,
            "client_secret": AMO_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": AMO_REDIRECT_URI
        }, timeout=15)
        data = r.json()
        save_tokens(data["access_token"], data["refresh_token"], data["expires_in"])
        return "✅ OAuth успешно! Токены сохранены.", 200
    except Exception as e:
        return f"Error: {e}", 500

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
                lead_name = (form.get(f"{p}[name]") or [""])[0]
                threading.Thread(target=process_lead_with_api, args=(lead_id, lead_name)).start()

            idx += 1

    return "OK", 200

@app.route("/", methods=["GET"])
def health():
    tokens = load_tokens()
    if tokens:
        return "✅ OK - токены есть", 200
    return "⚠️ OK - нет OAuth токенов, нужна авторизация", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
