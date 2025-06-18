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

# def send_whatsapp_message():
#     st.title("WhatsApp Message Sender")
#     phone_numbers = st.text_area(
#         "Enter phone numbers (one per line, with country code, e.g., +1234567890):"
#     )
#     numbers_list = [num.strip() for num in phone_numbers.splitlines() if num.strip()]
#     phone_number = st.text_input("Enter the phone number (with country code, e.g., +1234567890):")
#     message = st.text_area("Enter your message:")
#     hour = st.number_input("Hour (24-hour format):", min_value=0, max_value=23, value=12)
#     minute = st.number_input("Minute:", min_value=0, max_value=59, value=0)

#     if st.button("Send WhatsApp Message"):
#         if phone_number and message:
#             try:
#                 pwk.sendwhatmsg(phone_number, message, hour, minute)
#                 st.success(f"Message scheduled to be sent to {phone_number} at {hour}:{minute}.")
#             except Exception as e:
#                 st.error(f"Error: {e}")
#         elif numbers_list:
#             for number in numbers_list:
#                 try:
#                     pwk.sendwhatmsg(number, message, hour, minute)
#                     st.success(f"Message scheduled to be sent to {number} at {hour}:{minute}.")
#                 except Exception as e:
#                     st.error(f"Error sending message to {number}: {e}")   
#         else:
#             st.error("Please enter a valid phone number and message.")     



# 

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

    # Image upload
    uploaded_file = st.file_uploader("Upload an Image (optional)", type=["jpg", "jpeg", "png"])
    img_temp_path = None
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)

        # Save to temporary path
        img_temp_path = "temp_uploaded_image.jpg"
        with open(img_temp_path, "wb") as f:
            f.write(uploaded_file.read())

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

        # Progress setup
        progress_bar = st.progress(0)
        status_text = st.empty()
        success_count = 0
        error_count = 0

        for i, number in enumerate(numbers_list):
            try:
                status_text.text(f"📤 Sending message to {number}...")

                if not number.startswith('+'):
                    st.error(f"❌ Invalid format for {number}. Must start with country code (+)")
                    error_count += 1
                    continue

                if i == 0:
                    if img_temp_path:
                        pwk.sendwhats_image(
                            receiver=number,
                            img_path=img_temp_path,
                            caption=message,
                            # time_hour=hour,
                            # time_min=minute,
                            wait_time=15,
                            tab_close=True,
                            close_time=3
                        )
                    else:
                        pwk.sendwhatmsg(
                            phone_no=number,
                            message=message,
                            time_hour=hour,
                            time_min=minute,
                            wait_time=15,
                            tab_close=True,
                            close_time=3
                        )
                else:
                    if img_temp_path:
                        pwk.sendwhats_image(
                            receiver=number,
                            img_path=img_temp_path,
                            caption=message,
                            wait_time=15,
                            tab_close=True,
                            close_time=3
                        )
                    else:
                        pwk.sendwhatmsg_instantly(
                            phone_no=number,
                            message=message,
                            wait_time=15,
                            tab_close=True,
                            close_time=3
                        )

                st.success(f"✅ Message sent/scheduled to {number}")
                success_count += 1

                if i < len(numbers_list) - 1:
                    time.sleep(2)

            except Exception as e:
                st.error(f"❌ Error sending to {number}: {str(e)}")
                error_count += 1

            progress_bar.progress((i + 1) / len(numbers_list))

        status_text.text("✅ Process completed!")

        # Summary
        st.write("### Summary")
        st.write(f"✅ Successfully sent/scheduled: {success_count}")
        if error_count:
            st.write(f"❌ Failed: {error_count}")

        # Cleanup
        if img_temp_path and os.path.exists(img_temp_path):
            os.remove(img_temp_path)
            st.info("🧹 Temporary image file deleted.")

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
    

# from datetime import datetime, timedelta
# import time
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException, NoSuchElementException
# import os

# def launch_driver():
#     options = Options()
    
#     # Simple Chrome options without user data directory
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("--disable-gpu")
#     options.add_argument("--disable-extensions")
#     options.add_argument("--disable-plugins")
#     options.add_argument("--disable-web-security")
#     options.add_argument("--allow-running-insecure-content")
#     options.add_argument("--disable-background-timer-throttling")
#     options.add_argument("--disable-backgrounding-occluded-windows")
#     options.add_argument("--disable-renderer-backgrounding")
#     options.add_argument("--disable-features=TranslateUI")
#     options.add_argument("--disable-ipc-flooding-protection")
    
#     # Window options
#     options.add_argument("--start-maximized")
#     options.add_argument("--window-size=1920,1080")
    
#     # Use incognito mode to avoid conflicts
#     options.add_argument("--incognito")
    
#     # Additional stability options with random port
#     import random
#     debug_port = random.randint(9000, 9999)
#     options.add_argument(f"--remote-debugging-port={debug_port}")
#     options.add_argument("--disable-blink-features=AutomationControlled")
#     options.add_experimental_option("excludeSwitches", ["enable-automation"])
#     options.add_experimental_option('useAutomationExtension', False)
    
#     # Prefs to disable notifications and popups
#     prefs = {
#         "profile.default_content_setting_values.notifications": 2,
#         "profile.default_content_settings.popups": 0,
#         "profile.managed_default_content_settings.images": 2
#     }
#     options.add_experimental_option("prefs", prefs)
    
#     try:
#         driver = webdriver.Chrome(options=options)
#         driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
#         driver.get("https://web.whatsapp.com")
#         st.success("✅ Chrome launched successfully in incognito mode!")
#         st.warning("⚠️ You'll need to scan the QR code to log into WhatsApp Web")
#         return driver
#     except Exception as e:
#         st.error(f"Failed to launch Chrome: {str(e)}")
        
#         # Try even more basic options
#         st.info("Trying with minimal options...")
#         try:
#             basic_options = Options()
#             basic_options.add_argument("--no-sandbox")
#             basic_options.add_argument("--disable-dev-shm-usage")
            
#             driver = webdriver.Chrome(options=basic_options)
#             driver.get("https://web.whatsapp.com")
#             st.warning("⚠️ Basic mode - scan QR code to login")
#             return driver
#         except Exception as e2:
#             st.error(f"Even basic launch failed: {str(e2)}")
#             st.error("**MANUAL FIX REQUIRED:**")
#             st.write("1. **Open Task Manager** (Ctrl+Shift+Esc)")
#             st.write("2. **End ALL chrome.exe processes**")
#             st.write("3. **Close all Chrome windows completely**")
#             st.write("4. **Delete any WhatsApp_UserData_* folders** in your project directory")
#             st.write("5. **Try running the script again**")
#             st.write("6. **If still failing, restart your computer**")
#             raise

# def send_message(driver, phone_number, message):
#     try:
#         # Open chat via wa.me link
#         link = f"https://wa.me/{phone_number[1:]}"  # remove "+" from phone number
#         st.info(f"Opening WhatsApp link: {link}")
#         driver.get(link)
        
#         # Wait for page to load
#         wait = WebDriverWait(driver, 20)
#         time.sleep(3)
        
#         # Try multiple ways to find and click "Continue to Chat" button
#         continue_clicked = False
#         continue_selectors = [
#             (By.LINK_TEXT, "Continue to Chat"),
#             (By.PARTIAL_LINK_TEXT, "Continue"),
#             (By.PARTIAL_LINK_TEXT, "Chat"),
#             (By.XPATH, "//a[contains(text(), 'Continue')]"),
#             (By.XPATH, "//a[contains(text(), 'Chat')]"),
#             (By.CSS_SELECTOR, "a[href*='web.whatsapp.com']")
#         ]
        
#         for selector_type, selector_value in continue_selectors:
#             try:
#                 continue_btn = wait.until(EC.element_to_be_clickable((selector_type, selector_value)))
#                 continue_btn.click()
#                 st.success("✅ Clicked 'Continue to Chat'")
#                 continue_clicked = True
#                 break
#             except TimeoutException:
#                 continue
        
#         if not continue_clicked:
#             st.warning("Could not find 'Continue to Chat' button, trying direct WhatsApp Web...")
#             driver.get("https://web.whatsapp.com")
#             time.sleep(5)
        
#         time.sleep(3)
        
#         # Try to find WhatsApp Web button
#         web_clicked = False
#         if continue_clicked:
#             web_selectors = [
#                 (By.LINK_TEXT, "use WhatsApp Web"),
#                 (By.PARTIAL_LINK_TEXT, "WhatsApp Web"),
#                 (By.PARTIAL_LINK_TEXT, "Web"),
#                 (By.XPATH, "//a[contains(text(), 'Web')]"),
#                 (By.CSS_SELECTOR, "a[href*='web.whatsapp.com']")
#             ]
            
#             for selector_type, selector_value in web_selectors:
#                 try:
#                     web_btn = wait.until(EC.element_to_be_clickable((selector_type, selector_value)))
#                     web_btn.click()
#                     st.success("✅ Clicked 'WhatsApp Web'")
#                     web_clicked = True
#                     break
#                 except TimeoutException:
#                     continue
        
#         # Wait for WhatsApp Web to load
#         time.sleep(8)
        
#         # If we have a phone number, try to search for the contact
#         if not web_clicked and continue_clicked:
#             try:
#                 # Try to find search box and search for the number
#                 search_selectors = [
#                     (By.XPATH, "//div[@contenteditable='true'][@data-tab='3']"),
#                     (By.XPATH, "//div[@title='Search input textbox']"),
#                     (By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='3']")
#                 ]
                
#                 for selector_type, selector_value in search_selectors:
#                     try:
#                         search_box = wait.until(EC.element_to_be_clickable((selector_type, selector_value)))
#                         search_box.click()
#                         search_box.clear()
#                         search_box.send_keys(phone_number)
#                         time.sleep(2)
                        
#                         # Click on first result
#                         first_result = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-testid='cell-frame-container']")))
#                         first_result.click()
#                         st.success("✅ Found contact via search")
#                         break
#                     except TimeoutException:
#                         continue
#             except:
#                 pass

#         # Now try to find message box with multiple selectors
#         message_selectors = [
#             (By.XPATH, "//div[@title='Type a message']"),
#             (By.XPATH, "//div[@data-tab='10']"),
#             (By.XPATH, "//div[@contenteditable='true'][@data-tab='10']"),
#             (By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='10']"),
#             (By.CSS_SELECTOR, "div[title='Type a message']"),
#             (By.XPATH, "//div[contains(@class, 'copyable-text')][@contenteditable='true']")
#         ]
        
#         msg_box = None
#         for selector_type, selector_value in message_selectors:
#             try:
#                 msg_box = wait.until(EC.presence_of_element_located((selector_type, selector_value)))
#                 st.success("✅ Found message box")
#                 break
#             except TimeoutException:
#                 continue
        
#         if not msg_box:
#             # Take screenshot for debugging
#             driver.save_screenshot("whatsapp_error.png")
#             return False, "Could not find message input box. Screenshot saved as 'whatsapp_error.png'"
        
#         # Clear and type message
#         msg_box.click()
#         time.sleep(1)
#         msg_box.clear()
#         msg_box.send_keys(message)
#         time.sleep(1)
        
#         # Find and click send button with multiple selectors
#         send_selectors = [
#             (By.XPATH, "//button[@aria-label='Send']"),
#             (By.XPATH, "//span[@data-testid='send']"),
#             (By.CSS_SELECTOR, "button[aria-label='Send']"),
#             (By.XPATH, "//button[contains(@class, 'compose-btn-send')]"),
#             (By.XPATH, "//div[@role='button'][@aria-label='Send']")
#         ]
        
#         send_btn = None
#         for selector_type, selector_value in send_selectors:
#             try:
#                 send_btn = wait.until(EC.element_to_be_clickable((selector_type, selector_value)))
#                 break
#             except TimeoutException:
#                 continue
        
#         if not send_btn:
#             return False, "Could not find send button"
        
#         send_btn.click()
#         time.sleep(2)  # Wait for message to be sent
#         st.success("✅ Message sent successfully")
#         return True, ""
        
#     except TimeoutException as e:
#         driver.save_screenshot("timeout_error.png")
#         return False, f"Timeout waiting for element. Screenshot saved. Error: {str(e)}"
#     except NoSuchElementException as e:
#         driver.save_screenshot("element_not_found.png")
#         return False, f"Element not found. Screenshot saved. Error: {str(e)}"
#     except Exception as e:
#         driver.save_screenshot("general_error.png")
#         return False, f"General error. Screenshot saved. Error: {str(e)}"

# def validate_phone_number(number):
#     if not number.startswith('+'):
#         return False, "Must start with country code (+)"
#     if not number[1:].isdigit():
#         return False, "Digits only after '+'"
#     if len(number[1:]) < 10 or len(number[1:]) > 15:
#         return False, "Length should be 10–15 digits"
#     return True, "Valid"

# def send_whatsapp_message():
#     st.title("📤 WhatsApp Message Sender (Selenium)")
#     st.info("Make sure WhatsApp Web is logged in on your browser.")

#     input_numbers = st.text_area(
#         "Enter phone numbers (one per line, with country code, e.g., +1234567890):",
#         placeholder="+1234567890\n+9876543210"
#     )

#     message = st.text_area("Enter your message:")

#     col1, col2 = st.columns(2)
#     with col1:
#         hour = st.number_input("Hour (24h)", 0, 23, value=datetime.now().hour)
#     with col2:
#         minute = st.number_input("Minute", 0, 59, value=(datetime.now().minute + 2) % 60)

#     numbers_list = [num.strip() for num in input_numbers.splitlines() if num.strip()]

#     if st.button("Send Message", type="primary"):
#         if not numbers_list:
#             st.error("Enter at least one phone number.")
#             return
#         if not message.strip():
#             st.error("Message can't be empty.")
#             return

#         now = datetime.now()
#         scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
#         if scheduled <= now:
#             scheduled = scheduled + timedelta(days=1)  # Schedule for next day if time has passed
            
#         wait_time = (scheduled - now).total_seconds()
        
#         if wait_time > 0:
#             st.success(f"⏳ Waiting {int(wait_time)} seconds until scheduled time...")
            
#             # Create a progress bar for waiting time
#             wait_progress = st.progress(0)
#             wait_status = st.empty()
            
#             for i in range(int(wait_time)):
#                 wait_progress.progress((i + 1) / wait_time)
#                 remaining = int(wait_time - i)
#                 wait_status.text(f"Waiting... {remaining} seconds remaining")
#                 time.sleep(1)
            
#             wait_status.text("Starting to send messages...")

#         try:
#             driver = launch_driver()
#             st.info("Waiting for WhatsApp Web to load... Please ensure you're logged in.")
#             time.sleep(15)  # Give time to load WhatsApp Web

#             success = 0
#             fail = 0
#             progress = st.progress(0)
#             status = st.empty()

#             for i, number in enumerate(numbers_list):
#                 status.text(f"Sending to {number}...")
#                 valid, msg = validate_phone_number(number)
#                 if not valid:
#                     st.error(f"{number}: {msg}")
#                     fail += 1
#                 else:
#                     ok, error = send_message(driver, number, message)
#                     if ok:
#                         st.success(f"✅ Sent to {number}")
#                         success += 1
#                     else:
#                         st.error(f"❌ Failed to send to {number}: {error}")
#                         fail += 1

#                 progress.progress((i + 1) / len(numbers_list))
#                 if i < len(numbers_list) - 1:
#                     time.sleep(3)  # Wait between messages

#             status.text("✅ Done")
#             st.write("### Summary")
#             st.write(f"✅ Sent: {success}")
#             st.write(f"❌ Failed: {fail}")
            
#         except Exception as e:
#             st.error(f"Driver error: {str(e)}")
#             st.write("### Troubleshooting Steps:")
#             st.write("1. **Close all Chrome windows** and try again")
#             st.write("2. **Delete User_Data folder** if it exists in your project directory")
#             st.write("3. **Update ChromeDriver**: Download from https://chromedriver.chromium.org/")
#             st.write("4. **Check Chrome version**: chrome://version in browser")
#             st.write("5. **Run as administrator** if on Windows")
#             st.write("6. **Disable antivirus** temporarily")
#             st.write("7. **Try headless mode** by adding `--headless` option")
#         finally:
#             try:
#                 if 'driver' in locals():
#                     driver.quit()
#             except:
#                 pass

# # Sidebar
# with st.sidebar:
#     st.header("📋 Instructions")
#     st.write("""
#     1. Ensure WhatsApp Web is logged in.
#     2. Enter full international phone numbers.
#     3. Enter message and time (2+ mins ahead).
#     4. Keep this app and browser open until done.
#     5. Make sure Chrome browser is installed.
#     """)
    
#     st.header("⚠️ Troubleshooting")
#     st.write("""
#     - If elements aren't found, WhatsApp may have updated their interface
#     - Ensure stable internet connection
#     - Don't interact with the browser while sending
#     - Close other Chrome instances if issues occur
#     """)











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