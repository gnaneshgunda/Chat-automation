import streamlit as st
import pywhatkit as pwk
from datetime import datetime
import time
from PIL import Image
import os



st.set_page_config(
    page_title="WhatsApp Message Sender",
    page_icon="📱",
    layout="centered"
)
st.sidebar.title("Select your application")
app = st.sidebar.selectbox(
    "Select Application",
    options=["WhatsApp", "GMail"],
    index=0
)

import streamlit as st
import pywhatkit as pwk
import time
import os
from datetime import datetime
from PIL import Image
import hashlib

def send_whatsapp_message():
    st.title("📤 WhatsApp Message Sender")
    st.info("📱 Make sure WhatsApp Web is logged in on your default browser before sending messages.")

    # Phone numbers input
    input_numbers = st.text_area(
        "Enter phone numbers (one per line, with country code, e.g., +1234567890):",
        placeholder="+1234567890\n+9876543210"
    )

    # Message input
    message = st.text_area(
        "Enter your message:",
        placeholder="Hello! This is an automated message."
    )

    # Time scheduling
    col1, col2 = st.columns(2)
    with col1:
        hour = st.number_input("Hour (24-hour format):", min_value=0, max_value=23, value=datetime.now().hour)
    with col2:
        minute = st.number_input("Minute:", min_value=0, max_value=59, value=(datetime.now().minute + 2) % 60)

    # Process phone numbers
    numbers_list = [num.strip() for num in input_numbers.splitlines() if num.strip()]

    # Image upload - OPTIMIZED: Download once, reuse, delete at end
    uploaded_file = st.file_uploader("Upload an Image (optional)", type=["jpg", "jpeg", "png"])
    img_temp_path = None
    
    if uploaded_file is not None:
        # Create a unique filename based on file content hash
        file_content = uploaded_file.read()
        file_hash = hashlib.md5(file_content).hexdigest()
        img_temp_path = f"temp_image_{file_hash}.jpg"
        
        # Save image only if it doesn't exist (avoid re-downloading)
        if not os.path.exists(img_temp_path):
            with open(img_temp_path, "wb") as f:
                f.write(file_content)
            st.success("📥 Image saved temporarily for sending")
        else:
            st.info("📁 Using previously saved image")
        
        # Display the image
        image = Image.open(img_temp_path)
        st.image(image, caption="Uploaded Image", use_container_width=True)

    # Show parsed numbers
    if numbers_list:
        st.write(f"📞 Found {len(numbers_list)} phone number(s):")
        for i, num in enumerate(numbers_list, 1):
            st.write(f"{i}. {num}")

    # Send button
    if st.button("Send WhatsApp Message", type="primary"):
        if not numbers_list:
            st.error("❌ Please enter at least one phone number.")
            return
        if not message.strip():
            st.error("❌ Please enter a message.")
            return

        # Time check
        current_time = datetime.now()
        scheduled_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if scheduled_time <= current_time:
            st.warning("⚠️ Scheduled time should be at least 1-2 minutes in the future.")
            return

        # Verify image file exists if image was uploaded
        if img_temp_path and not os.path.exists(img_temp_path):
            st.error(f"❌ Image file not found: {img_temp_path}")
            return

        # Progress setup
        progress_bar = st.progress(0)
        status_text = st.empty()
        success_count = 0
        error_count = 0

        # Send messages to all numbers
        for i, number in enumerate(numbers_list):
            try:
                status_text.text(f"📤 Sending message to {number}...")

                if not number.startswith('+'):
                    st.error(f"❌ Invalid format for {number}. Must start with country code (+)")
                    error_count += 1
                    continue

                # Send message (with or without image)
                if i == 0:  # First message - use scheduled time
                    if img_temp_path:
                        pwk.sendwhats_image(
                            receiver=number,
                            img_path=img_temp_path,
                            caption=message,
                            wait_time=13,
                            tab_close=True,
                            close_time=5
                        )
                    else:
                        pwk.sendwhatmsg(
                            phone_no=number,
                            message=message,
                            time_hour=hour,
                            time_min=minute,
                            wait_time=13,
                            tab_close=True,
                            close_time=5
                        )
                else:  # Subsequent messages - send instantly
                    if img_temp_path:
                        pwk.sendwhats_image(
                            receiver=number,
                            img_path=img_temp_path,
                            caption=message,
                            wait_time=13,
                            tab_close=True,
                            close_time=5
                        )
                    else:
                        pwk.sendwhatmsg_instantly(
                            phone_no=number,
                            message=message,
                            wait_time=13,
                            tab_close=True,
                            close_time=5
                        )

                st.success(f"✅ Message sent/scheduled to {number}")
                success_count += 1

               

            except Exception as e:
                st.error(f"❌ Error sending to {number}: {str(e)}")
                error_count += 1

            # Update progress
            progress_bar.progress((i + 1) / len(numbers_list))

        status_text.text("✅ Process completed!")

        # Show summary
        st.write("### 📊 Summary")
        st.write(f"✅ Successfully sent/scheduled: {success_count}")
        if error_count:
            st.write(f"❌ Failed: {error_count}")

        # CLEANUP: Delete temporary image file
        if img_temp_path and os.path.exists(img_temp_path):
            try:
                time.sleep(2)  # Wait a moment before cleanup
                os.remove(img_temp_path)
                st.success("🧹 Temporary image file deleted successfully!")
            except Exception as e:
                st.warning(f"⚠️ Could not delete temporary file: {e}")

    # Sidebar with instructions
    with st.sidebar:
        st.header("📋 Instructions")
        st.write("""
        1. **Login to WhatsApp Web** in your default browser
        2. **Enter phone numbers** with country codes (e.g., +1234567890)
        3. **Write your message**
        4. **Upload image** (optional)
        5. **Set time** at least 2 minutes from now
        6. **Click Send** and keep browser open
        
        **Important:**
        - Don't use your computer during sending
        - Messages are sent via WhatsApp Web
        - Ensure stable internet connection
        - Image is saved once and reused for all contacts
        """)

        st.header("🔧 Troubleshooting")
        st.write("""
        **Common Issues:**
        - WhatsApp Web not logged in
        - Time set in the past
        - Invalid phone number format
        - Browser blocked by antivirus
        - Unstable internet connection
        - Image file too large (try compressing)
        """)

        st.header("💡 Tips")
        st.write("""
        **Performance:**
        - Image is downloaded once and reused
        - Temporary files are auto-deleted
        - 3-second delay between messages
        - Increased wait times for reliability
        """)












import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_gmail_message():
    st.title("GMail Message Sender")
    recipient_email = st.text_input("Enter recipient's email address:")
    subject = st.text_input("Enter the subject of the email:")
    message = st.text_area("Enter your message:")
    sender_email = st.text_input("Enter your Gmail address:")
    sender_password = st.text_input("Enter your Gmail app password:", type="password")

    if st.button("Send GMail Message"):
        if recipient_email and subject and message and sender_email and sender_password:
            try:
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = recipient_email
                msg['Subject'] = subject
                msg.attach(MIMEText(message, 'plain'))
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, msg.as_string())
                server.quit()
                st.success(f"Email sent to {recipient_email} with subject '{subject}'.")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.error("Please fill in all fields.")






if app == "WhatsApp":
    send_whatsapp_message()

elif app == "GMail":
    send_gmail_message()

