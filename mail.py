import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_gmail_message():
    st.title("GMail Message Sender")
    recipient_email = st.text_input("Enter recipient's email address:")
    subject = st.text_input("Enter the subject of the email:")
    message = st.text_area("Enter your message:")
    sender_email = st.text_input("Enter your Gmail address:")
    sender_password = st.text_input("Enter your Gmail app password:", type="password")
    sender_email = "rupsaisr@gmail.com"
    sender_password = "phhc fdmy tlbk wppk"

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
