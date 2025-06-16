from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
import time
import pandas as pd
import keyboard as kb
import logging

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
        logging.error("An error occurred while sending the WhatsApp message", exc_info=True)
        return False
    return True


def send_whatsapp_img(webd, phone_no, caption=None):
    try:
        search_box = webd.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
        search_box.clear()
        search_box.send_keys(phone_no)
        search_box.send_keys('\n')
        time.sleep(0.25)
        
        input_box = webd.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
        # input_box.click()
        input_box.send_keys(Keys.CONTROL, 'v')  
        time.sleep(0.5)
        if caption:
            # print("Caption provided, sending caption")
            # input_box0 = webd.find_element(By.XPATH, '//div[@aria-label="Add a caption" and @role="textbox"]')
            # print("Caption box found, sending caption")
            # input_box0.click()
            lines = caption.split('\n')
            for i, line in enumerate(lines):
                # input_box0.send_keys(line)
                kb.write(line)
                # print(f"Sending line: {line}")
                if i != len(lines) - 1:
                    kb.send('shift+enter')
                # else:
                #     input_box0.send_keys('\n')
        time.sleep(0.2)
        kb.send('enter')
        time.sleep(0.8)
    except Exception as e:
        logging.error("An error occurred while sending the WhatsApp image", exc_info=True)
        return False
    return True