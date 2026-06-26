# Chat Automation

A Streamlit desktop app to send **WhatsApp messages** and **Gmail emails** — single or in bulk — through a simple web UI powered by Selenium.

---

## What It Does

| Mode | Description |
|---|---|
| **WhatsApp** | Send a single WhatsApp message to any number at a scheduled time |
| **WhatsApp Bulk** | Send personalised messages to multiple contacts via CSV + template |
| **GMail** | Send a single email via Gmail SMTP |
| **GMail Bulk** | Send personalised emails to multiple recipients via CSV + template |

---

## Prerequisites

- Python 3.8+
- One of: **Chrome**, **Edge**, or **Firefox** (already installed on your system)
- The matching **WebDriver** for your browser (see [Browser Setup](#browser-setup))
- A Gmail account with an **App Password** enabled (for Gmail modes)

---

## Setup

**1. Clone / download the project**

```bash
git clone https://github.com/your-username/Chat-automation.git
cd Chat-automation
```

**2. Create a virtual environment (recommended)**

```bash
python -m venv venv
source venv/bin/activate      # Linux / Mac
venv\Scripts\activate          # Windows
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

> `smtplib` and `email` are Python standard library modules — no install needed.

---

## Browser Setup

The app copies your existing browser profile so WhatsApp Web is already logged in.
**You must log in to WhatsApp Web in your browser at least once before running the app.**

### Chrome *(recommended)*

1. Open Chrome → go to `web.whatsapp.com` → scan the QR code
2. Install ChromeDriver matching your Chrome version:
   - Check version: `chrome://settings/help`
   - Download: https://chromedriver.chromium.org/downloads
   - Or auto-manage: `pip install webdriver-manager`
3. Close Chrome before clicking Send (to avoid profile lock)

### Edge

1. Open Edge → go to `web.whatsapp.com` → scan the QR code
2. Install EdgeDriver matching your Edge version:
   - Check version: `edge://settings/help`
   - Download: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/
3. Close Edge before clicking Send

### Firefox ⚠️ *Use with caution*

1. Install **geckodriver** and place it in your system PATH:
   - Download: https://github.com/mozilla/geckodriver/releases
2. Open Firefox → go to `web.whatsapp.com` → scan QR code
3. **Close Firefox completely** before clicking Send — if Firefox is open with the same profile, the profile copy will fail with a lock error
4. WhatsApp Web shows a *"use a supported browser"* banner in Firefox — **this is cosmetic only**, sending still works
5. Firefox does **not** support Chrome's anti-automation-detection flags — WhatsApp may be slightly more likely to flag automated behaviour
6. Voice/video call features in WhatsApp Web may not work in Firefox (unrelated to this app)

---

## Running the App

```bash
streamlit run main.py
```

Opens in your browser at `http://localhost:8501`.

---

## How to Use

### WhatsApp — Single Message

1. Select **WhatsApp** from the sidebar
2. Choose your browser (Chrome / Edge / Firefox)
3. Enter the phone number **with country code** — e.g. `+91XXXXXXXXXX` for India
4. Type your message (optional: attach an image)
5. Set the scheduled time (at least 2 minutes ahead)
6. Click **Send WhatsApp Message**
7. Keep the browser open until the message is sent

> ⚠️ Do not interact with the browser while it is sending — Selenium controls it.

### WhatsApp — Bulk Messages

1. Select **WhatsAppBulk** from the sidebar
2. Prepare a **CSV file** with phone number column and any other data:
   ```
   phone,name,date
   +91XXXXXXXXXX,Alice,Monday
   +91XXXXXXXXXX,Bob,Tuesday
   ```
3. Prepare a **TXT template** using `{fieldname}` placeholders:
   ```
   Hello {name}, your appointment is on {date}.
   ```
4. Upload both files → select the phone column → map template fields
5. Preview the message and click **Send Bulk WhatsApp Messages**

> Phone numbers **must include the country code** — numbers without `+` are skipped with a warning.  
> A 3-second delay is added between messages to avoid WhatsApp rate-limiting.

### GMail — Single Email

1. Select **GMail** from the sidebar
2. Enter recipient email, subject, and message
3. Enter your Gmail address and **App Password** (see [Getting a Gmail App Password](#getting-a-gmail-app-password))
4. Click **Send Email**

### GMail — Bulk Emails

1. Select **GmailBulk** from the sidebar
2. Prepare a **CSV file** with at minimum an `email` column (optional: `name`):
   ```
   email,name
   alice@example.com,Alice
   bob@example.com,Bob
   ```
3. Prepare a **TXT template** using `{name}` and `{email}` placeholders:
   ```
   Hi {name}, thanks for signing up with {email}!
   ```
4. Upload both files → enter your credentials → click **Send Bulk Emails**

> CSV must have fewer than 500 rows (Gmail daily send limit).

---

## Getting a Gmail App Password

Gmail requires an App Password instead of your regular password for SMTP:

1. Go to your Google Account → **Security**
2. Enable **2-Step Verification** (required)
3. Go to **App passwords** → generate one for "Mail"
4. Use the generated **16-character password** in the app

---

## Project Structure

```
Chat-automation/
├── main.py               # Entry point — Streamlit app with sidebar routing
├── whatsapp.py           # WhatsApp single message UI & scheduling
├── whatsapp_bulk.py      # WhatsApp bulk message UI
├── mail.py               # Gmail single email sender
├── mail_bulk.py          # Gmail bulk email sender
├── whats/
│   └── whatsutils.py     # Selenium automation for WhatsApp Web
├── requirements.txt
└── README.md
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| **Contact opens but message not sent** | WhatsApp Web may show a "Continue to chat" dialog — the app handles this automatically. Make sure WhatsApp Web is fully loaded (not showing QR code) before clicking Send |
| **WhatsApp Web shows QR code** | Log in to WhatsApp Web in your browser first, then run the app |
| **Driver version mismatch** | Update your WebDriver to match your browser version |
| **"Profile in use" / lock error** | Close the browser completely before clicking Send |
| **Gmail "Authentication failed"** | Use an App Password, not your regular Gmail password. Enable 2-Step Verification first |
| **Firefox "supported browser" warning** | Cosmetic only — ignore it, sending works |
| **Messages not going in bulk** | Ensure phone numbers have country code (`+91...`). Numbers without `+` are skipped |

---

## Notes

- **Never commit credentials** — enter Gmail passwords in the UI only, never in code
- WhatsApp Web automation works by controlling your browser — keep it in the foreground during sends
- Gmail bulk is limited to 500 emails per run (Gmail's daily limit is ~500 for free accounts)
