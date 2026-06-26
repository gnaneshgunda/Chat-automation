"""
main.py — Chat Automation entry point (Streamlit).
Routes between WhatsApp / Gmail single & bulk senders.
"""

import streamlit as st
from mail_bulk import send_gmail_bulk_message
from mail import send_gmail_message
from whatsapp import send_whatsapp_message
from whatsapp_bulk import send_whatsapp_bulk_message

st.set_page_config(
    page_title="Chat Automation",
    page_icon="📱",
    layout="centered",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("📱 Chat Automation")
app = st.sidebar.selectbox(
    "Select Mode",
    options=["WhatsApp", "GMail", "GmailBulk", "WhatsAppBulk"],
    index=0,
)

with st.sidebar:
    st.markdown("---")

    # ── WhatsApp Quick-Start ──────────────────────────────────────────────────
    with st.expander("📋 WhatsApp — Quick Start", expanded=False):
        st.markdown("""
1. **Log in to WhatsApp Web** in Chrome or Edge  
   → open `web.whatsapp.com` and scan the QR code  
2. **Enter the phone number** with country code  
   (e.g. `+91XXXXXXXXXX` for India, `+1XXXXXXXXXX` for USA)  
3. **Write your message**  
4. **Set the scheduled time** (at least 2 minutes ahead)  
5. **Click Send** — keep the browser window open  

⚠️ Don't use the browser manually while sending  
⚠️ Keep your internet connection stable  
""")

    # ── Gmail Quick-Start ─────────────────────────────────────────────────────
    with st.expander("📧 Gmail — Quick Start", expanded=False):
        st.markdown("""
1. **Enable 2-Step Verification** on your Google Account  
2. Go to **Security → App passwords**  
3. Generate a password for "Mail"  
4. Use that **16-character App Password** in the app  
   (do NOT use your regular Gmail password)  
5. For bulk: prepare a **CSV** with an `email` column  
   and a **.txt template** using `{name}` / `{email}` placeholders  
""")

    # ── Browser Notes ─────────────────────────────────────────────────────────
    with st.expander("🌐 Browser Setup Notes", expanded=False):
        st.markdown("""
**Chrome**  
- Make sure `chromedriver` version matches your Chrome version  
- Profile is auto-copied from `~/.config/google-chrome/Default`  
- Close all Chrome windows before running to avoid profile lock  

**Edge** *(default / recommended)*  
- Make sure `msedgedriver` matches your Edge version  
- Profile is auto-copied from `~/.config/microsoft-edge/Default`  
- Close all Edge windows before running  

**Firefox** ⚠️ *Use with caution*  
- Requires `geckodriver` installed and in your system PATH  
  → [Download geckodriver](https://github.com/mozilla/geckodriver/releases)  
- WhatsApp Web will show a *"use a supported browser"* banner  
  — this is cosmetic, sending still works  
- **Close Firefox completely** before running or you'll get a  
  "profile in use" / lock error  
- Some WhatsApp Web features (voice, video) may not work in Firefox  
- Firefox does NOT support Chrome's anti-detection flags  
""")

    # ── Troubleshooting ───────────────────────────────────────────────────────
    with st.expander("🔧 Troubleshooting", expanded=False):
        st.markdown("""
**Contact opens but message not sent**  
→ WhatsApp Web may need you to click "Continue to chat" once manually  
→ Ensure WhatsApp Web is fully loaded before clicking Send  

**WhatsApp Web not loading / QR code shown**  
→ Log in to WhatsApp Web in your browser first, then run the app  

**Driver version mismatch error**  
→ Chrome: update chromedriver to match Chrome  
→ Edge: update msedgedriver to match Edge  
→ Firefox: update geckodriver  

**Gmail authentication error**  
→ Use an **App Password**, not your Gmail password  
→ 2-Step Verification must be enabled first  

**Profile lock / "profile in use" error**  
→ Close the browser completely before clicking Send  

**Messages sending too fast (bulk)**  
→ There is a 3-second delay between messages (built-in)  
→ If still getting banned, reduce batch size  
""")

    st.markdown("---")
    st.caption("Chat Automation v2.0 · Selenium + Streamlit")


# ── Page routing ──────────────────────────────────────────────────────────────
if app == "WhatsApp":
    send_whatsapp_message()

elif app == "GMail":
    send_gmail_message()

elif app == "GmailBulk":
    send_gmail_bulk_message()

elif app == "WhatsAppBulk":
    send_whatsapp_bulk_message()