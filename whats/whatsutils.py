from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import time
import pandas as pd

def send_whatsapp_message(webd,phone_no, message):
    try:
        search_box = webd.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
        search_box.clear()
        search_box.send_keys(phone_no)
        search_box.send_keys('\n') 
        time.sleep(0.25)
        input_box = webd.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
        input_box.click()
        lines = message.split('\n')
        for i, line in enumerate(lines):
            input_box.send_keys(line)
            if i != len(lines) - 1:
                input_box.send_keys(Keys.SHIFT, Keys.ENTER)
        input_box.send_keys('\n')
        time.sleep(0.5)
    except Exception as e:
        return False
    return True




# browsertime = time.time() 
# for index, row in data.iterrows():
#     phone_no = str(row['Contact'])
#     message = row['Message']
#     if send_whatsapp_message(phone_no, message):
#         print(f"Message sent to {phone_no}")
#     else:
#         print(f"Failed to send message to {phone_no}")

# toatltime = time.time()
# print(f"Total time taken: {toatltime - starttime} seconds")
# print(f"Browser time taken: {browsertime - starttime} seconds")
# print(f"message sent time taken: {toatltime - browsertime} seconds")
# print("Number of messages sent:", len(data))
# print(f"Average time per message: {(toatltime - browsertime) / len(data)} seconds")
# while True:
#     time.sleep(1)
