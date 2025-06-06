import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd

def send_gmail_bulk_message():
    sender_email = st.text_input("Enter your Gmail address:", value=None)
    sender_password = st.text_input("Enter your Gmail password:", value=None, type="password")
    st.title("GMail Message Sender")
    st.write("use {name} to replace with name in template file")
    subject = st.text_input("Enter the subject of the email:")
    st.write("Upload a CSV file with recipient emails and a template file for the message.")
    file = st.file_uploader(label="Upload a CSV file with recipient emails", type=["csv"], accept_multiple_files=False, label_visibility="visible",)
    template = st.file_uploader(label="Upload a template file", type=["txt"], accept_multiple_files=False, label_visibility="visible",)
    if sender_email is None or sender_password is None:
        sender_email = "rupsaisr@gmail.com"
        sender_password = "phhc fdmy tlbk wppk"
    totalcount = 0
    errorcount = 0
    st.write("You can use {name} and {email} in the template file to personalize the message.")

    if st.button("Send GMail Message"):
        
        if file is not None:
            filedata = pd.read_csv(file)
            filedata = filedata.dropna(subset=['email'])  # Ensure 'email' column exists and is not empty
            filedata = filedata[filedata['email'].str.contains('@')]  # Filter rows with valid email format
            if len(filedata) > 500:
                st.error("The number of rows in the CSV file must be less than 500.")
                return
            # st.write(filedata)
        else :
            st.error("Please upload a CSV file with recipient emails.")
        if template is not None:
            message = template.read().decode('utf-8')
                
        else:
            st.error("Please upload a template file.")
        if subject and message and sender_email and sender_password:
            try:
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(sender_email, sender_password)
                st.write("Sending emails...")
            except Exception as e:
                st.error(f"Error: {e}")
                server.quit()
                return
            for _, row in filedata.iterrows():
                totalcount += 1
                recipient_email = row['email']
                personalized_message = message.replace("{name}", row.get('name', ''))
                personalized_message = personalized_message.replace("{email}", recipient_email)
                personalized_subject = subject.replace("{name}", row.get('name', ''))
                try:
                    msg = MIMEMultipart()
                    msg['From'] = sender_email
                    msg['To'] = recipient_email
                    msg['Subject'] = personalized_subject
                    msg.attach(MIMEText(personalized_message, 'plain'))
                    server.sendmail(sender_email, recipient_email, msg.as_string())
                    st.success(f"Email sent to {recipient_email} with subject '{personalized_subject}'.")
                except Exception as e:
                    st.error(f"Error sending email to {recipient_email}: {e}")
                    errorcount += 1
            server.quit()
            st.success(f"Total emails sent: {totalcount - errorcount}, Errors: {errorcount}")
                    
                    
                
       