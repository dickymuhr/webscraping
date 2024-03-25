from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import logging, time

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
        
def visibility_element_with_text_and_refresh(driver, locator, max_retries=3, wait_between_retries=1, wait_timeout=10):
    attempts = 0
    while attempts < max_retries:
        try:
            # Use WebDriverWait to wait for the element with the custom condition
            element = WebDriverWait(driver, wait_timeout).until(
                visibility_of_element_located_with_text(locator)
            )
            if element:
                return element
        except TimeoutException as e:
            logging.info(f"Attempt {attempts + 1}: Waiting for element timed out. {str(e)}")
        
        # If the attempt fails and max_retries hasn't been reached, refresh and retry
        if attempts < max_retries - 1:
            driver.refresh()
            logging.info(f"Page refreshed before attempt {attempts + 2}.")
            time.sleep(wait_between_retries)
        
        attempts += 1

    logging.error(f"Failed to find an element with locator {locator} after {max_retries} attempts.")
    return False
        
class element_to_be_clickable_with_text(object):
    def __init__(self, locator, text):
        self.locator = locator
        self.text = text

    def __call__(self, driver):
        try:
            # Use the existing condition to check if the element is clickable
            element = WebDriverWait(driver, 2).until(EC.element_to_be_clickable(self.locator))
            # Then check if the text matches
            if self.text in element.text.strip():
                return element
        except NoSuchElementException:
            pass
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