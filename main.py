import streamlit as st
from mail_bulk import send_gmail_bulk_message
from mail import send_gmail_message 
from whatsapp import send_whatsapp_message
from whatsapp_bulk import send_whatsapp_bulk_message

st.set_page_config(
    page_title="WhatsApp Message Sender",
    page_icon="📱",
    layout="centered"
)

st.sidebar.title("Select your application")
app = st.sidebar.selectbox(
    "Select Application",
    options=["WhatsApp", "GMail","GmailBulk", "WhatsAppBulk"],
    index=0
)

# Add sidebar with instructions
with st.sidebar:
        st.header("📋 Instructions")
        st.write("""
        1. **Login to WhatsApp Web** in your default browser
        2. **Enter phone numbers** with country codes (e.g., +1234567890)
        3. **Write your message**
        4. **Set time** at least 2 minutes from now
        5. **Click Send** and keep browser open
        
        **Important:**
        - Don't use your computer during sending
        - Messages are sent via WhatsApp Web
        - Ensure stable internet connection
        """)

        st.header("🔧 Troubleshooting")
        st.write("""
        **Common Issues:**
        - WhatsApp Web not logged in
        - Time set in the past
        - Invalid phone number format
        - Browser blocked by antivirus
        - Unstable internet connection
        """)
    

if app == "WhatsApp":
    send_whatsapp_message()

elif app == "GMail":
    send_gmail_message()

elif app == "GmailBulk":
    send_gmail_bulk_message()

elif app == "WhatsAppBulk":
    send_whatsapp_bulk_message()