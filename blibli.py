from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
import time
# from selenium.webdriver.common.selenium_manager import SeleniumManager

# chrome_options = Options()
# chrome_options.add_argument("--test-type")
# chrome_options.add_argument('--ignore-certificate-errors')
# chrome_options.add_argument('--disable-extensions')
# chrome_options.add_argument('disable-infobars')
# chrome_options.add_argument("--incognito")
# # chrome_options.add_argument("--headless")
# chrome_options.add_experimental_option("useAutomationExtension", False)
# chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
# driver = webdriver.Chrome(options=chrome_options)
options = uc.ChromeOptions()
driver = uc.Chrome(version_main=120, options=options)

base_url = "https://www.blibli.com"
keyword = "indomi cabe ijo karton"

driver.get(base_url)
search_input = driver.find_element(By.NAME, "search")
search_input.send_keys(keyword + Keys.ENTER)
time.sleep(10)
# Refresh the page
driver.refresh()
time.sleep(30)
driver.quit()