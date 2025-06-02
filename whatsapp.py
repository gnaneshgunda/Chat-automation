import streamlit as st
import pywhatkit as pwk
from datetime import datetime
import time

def send_whatsapp_message():
    st.title("WhatsApp Message Sender")
    
    # Instructions for users
    st.info("📱 Make sure WhatsApp Web is logged in on your default browser before sending messages.")
    
    input_numbers = st.text_area(
        "Enter phone numbers (one per line, with country code, e.g., +1234567890):",
        placeholder="+1234567890\n+9876543210"
    )
    
    message = st.text_area(
        "Enter your message:",
        placeholder="Hello! This is an automated message."
    )

    # Time selection with validation
    col1, col2 = st.columns(2)
    with col1:
        hour = st.number_input(
            "Hour (24-hour format):", 
            min_value=0, 
            max_value=23, 
            value=datetime.now().hour
        )
    with col2:
        minute = st.number_input(
            "Minute:", 
            min_value=0, 
            max_value=59, 
            value=(datetime.now().minute + 2) % 60  # Add 2 minutes buffer
        )

    # Process phone numbers
    numbers_list = [num.strip() for num in input_numbers.splitlines() if num.strip()]
    
    # Display parsed numbers
    if numbers_list:
        st.write(f"📞 Found {len(numbers_list)} phone number(s):")
        for i, num in enumerate(numbers_list, 1):
            st.write(f"{i}. {num}")

    # Validation and sending
    if st.button("Send WhatsApp Message", type="primary"):
        if not numbers_list:
            st.error("❌ Please enter at least one phone number.")
        elif not message.strip():
            st.error("❌ Please enter a message.")
        else:
            # Check if scheduled time is in the future
            current_time = datetime.now()
            scheduled_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if scheduled_time <= current_time:
                st.warning("⚠️ Scheduled time should be at least 1-2 minutes in the future.")
                return
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            success_count = 0
            error_count = 0
            
            for i, number in enumerate(numbers_list):
                try:
                    status_text.text(f"📤 Sending message to {number}...")
                    
                    # Validate phone number format
                    if not number.startswith('+'):
                        st.error(f"❌ Invalid format for {number}. Must start with country code (+)")
                        error_count += 1
                        continue
                    
                    # Send message with pywhatkit
                    pwk.sendwhatmsg(
                        phone_no=number, 
                        message=message, 
                        time_hour=hour, 
                        time_min=minute,
                        wait_time=15,  # Wait time for WhatsApp web to load
                        tab_close=True,
                        close_time=3   # Time before closing tab
                    )
                    
                    st.success(f"✅ Message scheduled to be sent to {number} at {hour:02d}:{minute:02d}")
                    success_count += 1
                    
                    # Add delay between messages to avoid issues
                    if i < len(numbers_list) - 1:  # Don't delay after last message
                        time.sleep(2)
                    
                except Exception as e:
                    st.error(f"❌ Error sending message to {number}: {str(e)}")
                    error_count += 1
                
                # Update progress
                progress_bar.progress((i + 1) / len(numbers_list))
            
            # Final status
            status_text.text("✅ Process completed!")
            
            # Summary
            st.write("### Summary")
            st.write(f"✅ Successfully scheduled: {success_count} messages")
            if error_count > 0:
                st.write(f"❌ Failed: {error_count} messages")
            
            # Important notes
            st.write("### Important Notes:")
            st.write("- Messages will be sent automatically at the scheduled time")
            st.write("- Keep your browser open until messages are sent")
            st.write("- Don't use your computer during the sending process")


def validate_phone_number(number):
    """Basic phone number validation"""
    if not number.startswith('+'):
        return False, "Phone number must start with country code (+)"
    
    # Remove '+' and check if remaining characters are digits
    digits_only = number[1:]
    if not digits_only.isdigit():
        return False, "Phone number can only contain digits after country code"
    
    if len(digits_only) < 10 or len(digits_only) > 15:
        return False, "Phone number length should be between 10-15 digits"
    
    return True, "Valid"