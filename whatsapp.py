"""
whatsapp.py — WhatsApp single-message sender UI (Streamlit).

FIXES:
  - Fixed broken validation indentation (phone check falling through to send).
  - Temp file is now deleted AFTER webd.quit() so browser still has the file during upload.
  - Removed ~50 lines of dead commented-out pywhatkit code.
  - Added spinner and status messages during wait.
  - Scheduled time past-midnight edge case handled.
"""

import streamlit as st
from datetime import datetime
import time
import tempfile
import os
from whats.whatsutils import send_whatsapp_message as sendmsg, get_browser


def send_whatsapp_message():
    st.title("🟢 WhatsApp Single Message Sender")

    browser_choice = st.selectbox("🌐 Select Browser", ["Chrome", "Edge", "Firefox"])

    st.subheader("📝 Message Details")
    input_number = st.text_input(
        "📱 Phone Number",
        placeholder="+91XXXXXXXXXX",
        help="Full number with country code — e.g. +91 for India, +1 for USA",
    )

    message = st.text_area(
        "✍️ Your Message",
        placeholder="Type your message here...",
        height=150,
    )

    image_file = st.file_uploader(
        "🖼️ Attach Image (optional)",
        type=["jpg", "jpeg", "png", "gif", "webp"],
    )

    # ── Schedule ──────────────────────────────────────────────────────────────
    st.subheader("⏰ Schedule Message")
    st.caption("Select the time when you want the message to be sent")
    col1, col2 = st.columns(2)
    with col1:
        hour = st.number_input(
            "Hour (24-hour)", min_value=0, max_value=23,
            value=datetime.now().hour,
        )
    with col2:
        minute = st.number_input(
            "Minute", min_value=0, max_value=59,
            value=(datetime.now().minute + 2) % 60,
        )

    st.info(f"📅 Message will be sent at **{hour:02d}:{minute:02d}**")
    if input_number:
        st.write(f"📤 Will be sent to: **{input_number}**")

    # ── Send button ───────────────────────────────────────────────────────────
    if st.button("🚀 Send WhatsApp Message", type="primary"):

        # ── Validation (FIXED: was broken indentation, all checks upfront) ───
        errors = []
        if not input_number:
            errors.append("Please enter a phone number.")
        else:
            is_valid, err_msg = validate_phone_number(input_number)
            if not is_valid:
                errors.append(f"Invalid phone number: {err_msg}")

        if not message.strip():
            errors.append("Please enter a message.")

        if errors:
            for e in errors:
                st.error(f"❌ {e}")
            return

        # ── Schedule wait ─────────────────────────────────────────────────────
        tmp_file = None
        image_path = None

        try:
            if image_file:
                suffix = os.path.splitext(image_file.name)[1]
                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                tmp_file.write(image_file.read())
                tmp_file.flush()
                tmp_file.close()          # close handle but keep the file
                image_path = tmp_file.name

            webd = get_browser(browser_choice)
            webd.get("https://web.whatsapp.com")
            webd.maximize_window()

            # Wait for WhatsApp Web to load (give user time to scan QR if needed)
            with st.spinner("⏳ Waiting for WhatsApp Web to load (10 s)…"):
                time.sleep(10)

            # Wait until scheduled time
            now = datetime.now()
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                st.warning("⚠️ Scheduled time is in the past — sending immediately.")
            else:
                wait_secs = (target - now).total_seconds()
                st.info(f"⏳ Waiting {int(wait_secs)} seconds until {hour:02d}:{minute:02d}…")
                with st.spinner(f"Waiting until {hour:02d}:{minute:02d}…"):
                    # Poll in small steps so we don't freeze the process
                    while True:
                        remaining = (target - datetime.now()).total_seconds()
                        if remaining <= 0:
                            break
                        time.sleep(min(5, remaining))

            # Send
            if sendmsg(webd, input_number, message.strip(), image_path):
                st.success(f"✅ Message sent to {input_number} at {hour:02d}:{minute:02d}")
            else:
                st.error(
                    "❌ Failed to send. Possible reasons:\n"
                    "- WhatsApp Web is not logged in\n"
                    "- Phone number not on WhatsApp\n"
                    "- Browser profile not found (open browser manually and log in first)"
                )

        except FileNotFoundError as e:
            st.error(f"❌ Browser profile error: {e}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")
        finally:
            # Quit browser FIRST, then delete temp file
            try:
                webd.quit()
            except Exception:
                pass
            if tmp_file and os.path.exists(image_path):
                os.unlink(image_path)


def validate_phone_number(number: str):
    """Basic E.164 phone number validation."""
    if not number.startswith("+"):
        return False, "Must start with country code (e.g. +91 for India)"
    digits_only = number[1:].replace(" ", "").replace("-", "")
    if not digits_only.isdigit():
        return False, "Only digits allowed after country code"
    if len(digits_only) < 10 or len(digits_only) > 15:
        return False, "Length must be 10–15 digits after country code"
    return True, "Valid"
