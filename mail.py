"""
mail.py — Gmail single-message sender (Streamlit).

FIXES:
  - Added recipient email format validation.
  - SMTP connection now always closed via finally block.
  - Better error messages (auth vs network vs unknown).
"""

import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_gmail_message():
    st.title("📧 Gmail Message Sender")

    st.info(
        "💡 Use a **Gmail App Password**, not your account password.\n"
        "Enable at: Google Account → Security → 2-Step Verification → App passwords"
    )

    recipient_email = st.text_input("Recipient Email", placeholder="friend@example.com")
    subject         = st.text_input("Subject")
    message         = st.text_area("Message", height=150)
    sender_email    = st.text_input("Your Gmail Address", placeholder="you@gmail.com")
    sender_password = st.text_input("Gmail App Password", type="password", placeholder="xxxx xxxx xxxx xxxx")

    if st.button("📤 Send Email", type="primary"):

        # ── Validation ────────────────────────────────────────────────────────
        missing = []
        if not recipient_email:
            missing.append("recipient email")
        elif "@" not in recipient_email or "." not in recipient_email:
            st.error("❌ Recipient email address looks invalid.")
            return
        if not subject:
            missing.append("subject")
        if not message.strip():
            missing.append("message")
        if not sender_email:
            missing.append("your Gmail address")
        if not sender_password:
            missing.append("App Password")

        if missing:
            st.error(f"❌ Please fill in: {', '.join(missing)}")
            return

        # ── Send ──────────────────────────────────────────────────────────────
        server = None
        try:
            msg = MIMEMultipart()
            msg["From"]    = sender_email
            msg["To"]      = recipient_email
            msg["Subject"] = subject
            msg.attach(MIMEText(message, "plain"))

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.ehlo()
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())

            st.success(f"✅ Email sent to **{recipient_email}** with subject *{subject}*")

        except smtplib.SMTPAuthenticationError:
            st.error(
                "❌ Authentication failed. Use a **Gmail App Password**, not your regular password. "
                "Generate at: Google Account → Security → App passwords."
            )
        except smtplib.SMTPConnectError:
            st.error("❌ Could not connect to Gmail. Check your internet connection.")
        except Exception as e:
            st.error(f"❌ Error: {e}")
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass
