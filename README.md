# Chat Automation

A Streamlit desktop app to send **WhatsApp messages** and **Gmail emails** — single or in bulk — through a simple web UI powered by Selenium.

---

## What It Does

| Mode | Description |
|---|---|
| **WhatsApp** | Send a single WhatsApp message (text + optional image) to any number at a scheduled time |
| **WhatsApp Bulk** | Send personalised messages (text + optional image) to multiple contacts via CSV + template |
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
python -m venv path/to/venv
source path/to/venv/bin/activate      # Linux / Mac
path\to\venv\Scripts\activate          # Windows
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
   - Already included in `requirements.txt` via `webdriver-manager`
3. **Close Chrome before clicking Send** (to avoid profile lock)

### Edge

1. Open Edge → go to `web.whatsapp.com` → scan the QR code
2. Install EdgeDriver matching your Edge version:
   - Check version: `edge://settings/help`
   - Download: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/
3. **Close Edge before clicking Send**

### Firefox ⚠️ *Use with caution*

1. Install **geckodriver** and place it in your system PATH:
   - Download: https://github.com/mozilla/geckodriver/releases
2. Open Firefox → go to `web.whatsapp.com` → scan QR code
3. **Close Firefox completely** before clicking Send — if Firefox is open with the same profile, the profile copy will fail with a lock error
4. WhatsApp Web shows a *"use a supported browser"* banner in Firefox — **this is cosmetic only**, sending still works
5. Firefox does **not** support Chrome's anti-automation-detection flags — WhatsApp may be slightly more likely to flag automated behaviour

---

## Running the App

```bash
# Activate your virtual environment first
source path/to/venv/bin/activate   # Linux / Mac
path\to\venv\Scripts\activate       # Windows

streamlit run main.py
```

Opens in your browser at `http://localhost:8501`.

---

## How to Use

### WhatsApp — Single Message

1. Select **WhatsApp** from the sidebar
2. Choose your browser (Chrome / Edge / Firefox)
3. Enter the phone number **with country code** — e.g. `+91XXXXXXXXXX` for India
4. Type your message
5. *(Optional)* Attach an image — supported formats: `jpg`, `jpeg`, `png`, `gif`, `webp`
6. Set the scheduled time (set to current time to send immediately)
7. Click **🚀 Send WhatsApp Message**
8. Keep the automated browser window open and **do not interact with it** until the message is sent

> ⚠️ Close your browser before clicking Send — the app opens a new controlled session using your saved profile.

### WhatsApp — Bulk Messages

1. Select **WhatsAppBulk** from the sidebar
2. Prepare a **CSV file** with a phone number column and any custom data columns:
   ```
   phone,name,date
   +91XXXXXXXXXX,Alice,Monday
   +91XXXXXXXXXX,Bob,Tuesday
   ```
3. Prepare a **TXT template** using `{fieldname}` placeholders matching your CSV columns:
   ```
   Hello {name}, your appointment is on {date}.
   ```
4. *(Optional)* Attach an image to be sent with every message
5. Upload both files → select the phone column → map template fields → preview
6. Click **Send Bulk WhatsApp Messages**

> Phone numbers **must include the country code** (e.g. `+91...`). Numbers without `+` are skipped with a warning.  
> A delay is added between messages to avoid WhatsApp rate-limiting.

### GMail — Single Email

1. Select **GMail** from the sidebar
2. Enter recipient email, subject, and message body
3. Enter your Gmail address and **App Password** (see [Getting a Gmail App Password](#getting-a-gmail-app-password))
4. Click **Send Email**

### GMail — Bulk Emails

1. Select **GmailBulk** from the sidebar
2. Prepare a **CSV file** with at minimum an `email` column:
   ```
   email,name,offer
   alice@example.com,Alice,20%
   bob@example.com,Bob,15%
   ```
3. Prepare a **TXT template** using `{fieldname}` placeholders:
   ```
   Hi {name}, you have a special offer of {offer} waiting for you!
   ```
4. Upload both files → enter your credentials → click **Send Bulk Emails**

> CSV must have fewer than 500 rows (Gmail daily send limit for free accounts).

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
│   └── whatsutils.py     # Selenium automation core for WhatsApp Web
│                         #   • Multi-strategy image attach (A/B/C)
│                         #   • Photos & Videos menu click (avoids sticker mode)
│                         #   • Caption box anchor for safe media send
│                         #   • Multi-selector send button & fallbacks
├── requirements.txt
└── README.md
```

---

## Image Sending — How It Works

WhatsApp Web automation for images is complex because WA Web changes its DOM frequently. The app uses three strategies with automatic fallback:

| Strategy | Method |
|---|---|
| **A** | Click the attach button (JS click) → click **"Photos & Videos"** menu item → inject file into photo input |
| **B** | Directly inject file into the photo/video-specific file input (no menu click needed) |
| **C** | Try all `input[type=file]` elements that accept images/video, skipping sticker-only inputs |

After each strategy injects the file, the app:
1. Waits for the **media preview panel** (caption box) to appear
2. Types the caption (your message text) if provided
3. Sends via **Enter key** in the caption box
4. Falls back to DOM-walk send button search if Enter fails

> If the media preview does not open and the active element is the chat compose box, the app **aborts** to prevent sending text-only without the image.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| **Contact opens but message not sent** | The app handles the "Continue to chat" dialog automatically. Make sure WhatsApp Web is fully loaded (not showing QR code) before clicking Send |
| **WhatsApp Web shows QR code** | Log in to WhatsApp Web in your browser first, then close the browser and run the app |
| **Image sent as sticker** | Fixed in current version — the app now explicitly clicks "Photos & Videos" to avoid the sticker input |
| **Image not sent / preview didn't open** | A `wa_send_debug.png` screenshot is saved in the project folder — open it to see what WA Web is showing |
| **Caption not included with image** | Fixed — caption is now typed into the media preview panel's caption box directly |
| **"element click intercepted" error** | Fixed — the attach button click now uses JS click to bypass the compose-box overlay |
| **Driver version mismatch** | Update your WebDriver to match your browser version. For Chrome: `pip install --upgrade webdriver-manager` |
| **"Profile in use" / lock error** | Close the browser completely before clicking Send |
| **`No module named 'selenium'`** | Activate your virtual environment: `source path/to/venv/bin/activate`, then re-run |
| **Gmail "Authentication failed"** | Use an App Password, not your regular Gmail password. Enable 2-Step Verification first |
| **Firefox "supported browser" warning** | Cosmetic only — ignore it, sending works |
| **Messages not going in bulk** | Ensure phone numbers have country code (`+91...`). Numbers without `+` are skipped |

---

## Known Limitations

- WhatsApp Web selectors change with WA Web updates — if image sending breaks after a WA Web update, check the logs and the saved `wa_send_debug.png` screenshot
- Gmail bulk is limited to ~500 emails per run (Gmail's free daily send limit)
- The app controls a real browser session — do **not** interact with the browser window while it is sending

---

## Notes

- **Never commit credentials** — enter Gmail passwords in the UI only, never in code
- WhatsApp Web automation works by controlling your browser — keep the automated window visible during sends
- Tested on: Chrome 148, WA Web (June 2025), Ubuntu Linux
