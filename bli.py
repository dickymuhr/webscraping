from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from urllib.parse import quote
from fake_useragent import UserAgent
import undetected_chromedriver as uc
import logging, json, time, re
from helper import visibility_of_element_located_with_text, find_element_text_or_none, find_element_with_retries

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def wait_for_multiple_conditions(driver, timeout, *conditions):
    wait = WebDriverWait(driver, timeout)
    for condition in conditions:
        wait.until(condition)

ua = UserAgent()
user_agent = ua.random
options = uc.ChromeOptions()
options.add_argument(f'--user-agent={user_agent}')
options.add_argument('--disable-extensions')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox') 
options.add_argument("--headless")
options.add_argument('--disable-dev-shm-usage')
options.add_argument("--test-type")
options.add_argument('--ignore-certificate-errors')
options.add_argument('--disable-infobars')
options.add_argument("--incognito")

driver = uc.Chrome(version_main=120, options=options, use_subprocess=False)

def extract_product(driver, product_links):
    if product_links:  # Proceed only if product_links is not empty
        logging.info(f"Found {len(product_links)} products at page")
        hrefs = [link.get_attribute("href") for link in product_links]

        all_product_in_page = []
        page_times = []
        if hrefs:
            for href in hrefs:
                page_start_time = time.time()
                try:
                    driver.get(href)
                    logging.info(f"Accessing: {href}")

                    selling_price_element = WebDriverWait(driver, 15).until(
                        visibility_of_element_located_with_text((By.CLASS_NAME, "product-price__after"))
                    )
                    selling_price = selling_price_element.text.strip()
                    if not selling_price:
                        raise ValueError("Selling price is empty after waiting.")
                    
                    try:
                        original_price = driver.find_element(By.CLASS_NAME, "product-price__before").text
                    except NoSuchElementException:
                        original_price = None

                    product_name = driver.find_element(By.CLASS_NAME, "product-name").text

                    sold = find_element_text_or_none(driver, By.CLASS_NAME, "product-statistics__sold-seen")
                    rating_decimal = find_element_text_or_none(driver, By.CLASS_NAME, "product-rating__decimal")
                    rating_count = find_element_text_or_none(driver, By.CLASS_NAME, "product-rating__count")

                    category = driver.find_element(By.CSS_SELECTOR, 'span[data-testid="descriptionInfoCategory"]').text

                    item_elements = driver.find_elements(By.CSS_SELECTOR, ".hero-thumbnails .item:not(.video), .hero-thumbnails .item.selected:not(.video)")
                    # Extract 'data-src' from img elements within these item elements
                    img_urls = [item.find_element(By.TAG_NAME, "img").get_attribute('data-src') for item in item_elements]
                    img_urls = [item.replace("/thumbnail/", "/full/") for item in img_urls]

                    product_identifier = find_element_with_retries(driver, (By.CLASS_NAME, "product-identifier"))
                    sku_code = product_identifier.find_elements(By.CLASS_NAME, "value")[0].text
                    
                    if not sku_code.strip():  # Checks if the string is empty or whitespace
                        raise ValueError("SKU code is not available or empty.")
                    
                    specification_list_element = driver.find_element(By.CLASS_NAME, "specification__list")
                    specification_items = specification_list_element.find_elements(By.TAG_NAME, "li")
                    specifications_dict = {}
                    for item in specification_items:
                        label = item.find_element(By.CLASS_NAME, "label").text
                        value = item.find_element(By.CLASS_NAME, "value").text
                        specifications_dict[label] = value

                    description_div = driver.find_element(By.CSS_SELECTOR, 'div[description-nav-anchor="Deskripsi"]')
                    description_text = description_div.text

                    product_dict = {
                        "sku_code" : sku_code,
                        "product_name" : product_name,
                        "url" : href,
                        "image_urls" : img_urls,
                        "category" : category,
                        "selling_price" : selling_price,
                        "original_price" : original_price,
                        "total_sold" : sold,
                        "rating" : rating_decimal,
                        "rating_count" : rating_count,
                        "specifications" : specifications_dict,
                        "description" : description_text
                    }
                    page_end_time = time.time()
                    page_time = page_end_time - page_start_time
                    page_times.append(page_time) 

                    
                    
                    logging.info(f"Page processed in {page_time:.2f} seconds")
                    logging.info(json.dumps(product_dict, indent=4))
                    
                    all_product_in_page.append(product_dict)
                    
                except (TimeoutException,NoSuchElementException) as e:
                    with open("page_source.html", "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    driver.save_screenshot("debug_screenshot.png")
                    logging.warning(f"Detail product not showing up: {e}")
                    break

        if page_times:
            average_time = sum(page_times) / len(page_times)
            logging.info(f"Average time per page: {average_time:.2f} seconds for {len(page_times)} products")

        return all_product_in_page
    else:
        logging.info("No products found.")

domain_url = "https://www.blibli.com/"
search_api = "cari/"
keyword = "indomie cabe ijo"
encoded_keyword = quote(keyword)
sort_bestseller = "?sort=16" # &intent=false
starting_url = domain_url + search_api + encoded_keyword + sort_bestseller

logging.info(f"Accessing {starting_url}")
driver.get(starting_url)

total_product = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "product-listing-totalItem"))
)
logging.info(f"Found {total_product.text}")

product_links = []  # Initialize product_links before the try block
css_selector = "div.product__card.product__card__five div.product__container a"
try:
    product_links = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector))
    )
except TimeoutException as e:
    logging.warning("Timeout waiting for product links: " + str(e))
except Exception as e:
    logging.warning("General exception occurred: " + str(e))

product_page = extract_product(driver, product_links)
filename = keyword.replace(" ", "_") + ".json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(product_page, f, indent=4)

driver.quit()
