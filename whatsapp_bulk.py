import streamlit as st
import time
from whats.whatsutils import send_whatsapp_message as sendmsg
import pandas as pd
from selenium import webdriver

def send_whatsapp_bulk_message():
    st.title("WhatsApp Bulk Message Sender")
    st.info("📱 Make sure WhatsApp Web is logged in on your default browser before sending messages.")
    st.write("Use {name} to replace with name in template file.")
    st.write("Upload a CSV file with recipient phone numbers and a template file for the message.")
    file = st.file_uploader(label="Upload a CSV file with recipient phone numbers", type=["csv"], accept_multiple_files=False, label_visibility="visible",)
    template = st.file_uploader(label="Upload a template file", type=["txt"], accept_multiple_files=False, label_visibility="visible",)
    
    totalcount = 0
    errorcount = 0
    st.write("You can use {name} and {phone} in the template file to personalize the message.")

    if st.button("Send WhatsApp Bulk Message", type="primary"):
        if file is not None:
            filedata = pd.read_csv(file)
            filedata = filedata.dropna(subset=['phone'])  # Ensure 'phone' column exists and is not empty
            

            
        else :
            st.error("Please upload a CSV file with recipient emails.")
            return
        if template is not None:
            message_template = template.read().decode('utf-8')
        else:
            st.error("Please upload a template file.")
            return

        if message_template:
            try:
                webd = webdriver.Edge()
                webd.get("https://web.whatsapp.com")
                webd.maximize_window()
                webd.implicitly_wait(100)
                time.sleep(10)

                for _, row in filedata.iterrows():
                    totalcount += 1
                    recipient_phone = str(row['phone'])
                    personalized_message = message_template.replace("{name}", str(row.get('name', '')))
                    personalized_message = personalized_message.replace("{phone}", recipient_phone)
                    
                    if sendmsg(webd, recipient_phone, personalized_message):
                        st.success(f"Message sent to {recipient_phone}.")
                    else:
                        st.error(f"Failed to send message to {recipient_phone}.")
                        errorcount += 1
                        
            except Exception as e:
                st.error(f"An error occurred while sending messages: {str(e)}")
                if 'webd' in locals():
                    webd.quit()
            time.sleep(20)
            if 'webd' in locals():
                webd.quit()
            st.success(f"Total messages attempted: {totalcount}, Successfully sent: {totalcount - errorcount}, Errors: {errorcount}")
            st.session_state['whatsapp_logged_in'] = False # Reset login state



