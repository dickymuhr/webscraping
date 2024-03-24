from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class visibility_of_element_located_with_text(object):
    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        element = driver.find_element(*self.locator) # Find the element
        if element and element.is_displayed() and element.text.strip():
            return element
        else:
            return False
        
def find_element_text_or_none(driver, by, value):
    try:
        return driver.find_element(by, value).text
    except NoSuchElementException:
        return None
    
def find_element_with_retries(driver, locator, timeout=10, max_retries=3, refresh_before_retry=True):
    attempts = 0
    while attempts < max_retries:
        try:
            if attempts > 0 and refresh_before_retry:
                driver.refresh()
                logging.info(f"Attempt {attempts + 1}: Page refreshed.")
            
            return WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
        except TimeoutException as e:
            logging.info(f"Attempt {attempts + 1}: Waiting for element {locator} timed out.")
            attempts += 1
            
            if attempts == max_retries:
                logging.error(f"Failed to find element {locator} after {max_retries} attempts.")
                return None