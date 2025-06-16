import streamlit as st
import time
from whats.whatsutils import send_whatsapp_message as sendmsg
import pandas as pd
from selenium import webdriver

def send_whatsapp_bulk_message():
    st.title("📨 WhatsApp Bulk Message Sender")
    
    # Help and instructions
    with st.expander("ℹ️ How to use Bulk Message Sender", expanded=False):
        st.markdown("""
        **Features:**
        - Send personalized messages to multiple contacts
        - Support for CSV file upload
        - Message templating with custom fields
        
        **How to prepare your files:**
        1. **CSV File**: Create a spreadsheet with columns for phone numbers and other data
        2. **Template File**: Create a text file with your message and use {fieldname} for personalization
        
        **Example:**
        - CSV columns: phone, name, appointment
        - Template: "Hello {name}, your appointment is scheduled for {appointment}"
        """)
    
    # File upload section
    st.subheader("📁 Upload Your Files")
    col1, col2 = st.columns(2)
    
    with col1:
        file = st.file_uploader(
            "📊 Upload CSV file",
            type=["csv"],
            help="Upload a CSV file containing recipient phone numbers and other data"
        )
        
    with col2:
        template = st.file_uploader(
            "📝 Upload message template",
            type=["txt"],
            help="Upload a text file containing your message template"
        )
    
    st.info("💡 Pro tip: Make sure your CSV file has proper column headers and your template uses matching field names.")
    
    totalcount = 0
    errorcount = 0
    st.write("You can use {} in the template file to personalize the message.")
    if file is not None:
        filedata = pd.read_csv(file)
        st.dataframe(filedata.head(7))  # Display the first few rows of the uploaded CSV
        columns = filedata.columns.tolist()
        memo = {}
        isitname = st.checkbox("Will you use names for contact identification? default is phone number", help="If checked, names will be used instead of phone numbers (NOT RECOMMENDED)", value=False)
        phonecolumn = st.selectbox(f"Select the column containing {'names' if isitname else 'phone numbers'}", options=columns, index=0)
        st.markdown("---")
        for i in range(len(columns)):
            columns[i] = columns[i].strip().lower()
            st.dataframe(filedata[columns[i]].head(2))  # Display the first few rows of each column
            text = st.text_input(f"Enter column description for '{columns[i]}' leave it as it is to keep default and not use it feel free to delete it", value=columns[i])
            st.markdown("---")  # This adds a solid horizontal line in Streamlit
            if text:
                memo[columns[i]] = text

        filedata.columns = columns
        filedata = filedata.dropna(subset=[phonecolumn])  # Ensure selected column exists and is not empty
            
    if template is not None:
        message_template = template.read().decode('utf-8')
    else:
        st.error("Please upload a template file.")
        return
    if not file or not message_template:
        st.error("Please upload both a CSV file and a template file.")
        return
    st.markdown("---")
    
    personalized_message = message_template
    row = filedata.iloc[0]  
    for key, value in memo.items():
        if value.strip():
            if key in row:
                personalized_message = personalized_message.replace(f'{{{value}}}', str(row[key]))
    st.subheader("📋 Message Preview")
    st.write("This is how your message will look like when sent:")
    st.markdown(f"```\n{personalized_message}\n```")
            

    if st.button("Send WhatsApp Bulk Message", type="primary"):
        starttime = time.time()
        
        

        if message_template:
            try:
                webd = webdriver.Edge()
                webd.get("https://web.whatsapp.com")
                webd.maximize_window()
                webd.implicitly_wait(100)
                time.sleep(10)
                browsertime = time.time()
                for _, row in filedata.iterrows():
                    totalcount += 1
                    recipient_phone = str(row[phonecolumn]).strip()
                    # Only format phone number if not using names
                    if not isitname:
                        if not recipient_phone.startswith('+'):
                            recipient_phone = '+91' + recipient_phone
                    personalized_message = message_template
                    for key, value in memo.items():
                        if value.strip():
                            if key in row:
                                personalized_message = personalized_message.replace(f'{{{value}}}', str(row[key]))

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
                endtime = time.time()
                print(f"Time taken to send messages: {endtime - browsertime} seconds")
                print(f"Total time taken: {endtime - starttime} seconds")
                print(f"Avarage time for a message = {(endtime-browsertime)/totalcount}")
            st.success(f"Total messages attempted: {totalcount}, Successfully sent: {totalcount - errorcount}, Errors: {errorcount}")
            st.session_state['whatsapp_logged_in'] = False # Reset login state



