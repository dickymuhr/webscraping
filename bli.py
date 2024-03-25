from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from urllib.parse import quote
from fake_useragent import UserAgent
import undetected_chromedriver as uc
import logging, json, time
import pandas as pd
from sqlalchemy import create_engine, text
from helper import visibility_element_with_text_and_refresh, element_to_be_clickable_with_text,find_element_text_or_none, find_element_with_retries

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

def extract_product(driver, hrefs):
    if hrefs:  # Proceed only if product_links is not empty
        logging.info(f"Found {len(hrefs)} products")
    
        all_product_in_page = []
        page_times = []
        if hrefs:
            for href in hrefs:
                page_start_time = time.time()
                try:
                    driver.get(href)
                    logging.info(f"Accessing: {href}")

                    selling_price_element = visibility_element_with_text_and_refresh(
                        driver,
                        locator=(By.CLASS_NAME, "product-price__after"),
                        max_retries=3,  # Number of retries, adjust as needed
                        wait_between_retries=2,  # Time to wait between retries in seconds
                        wait_timeout=15  # Timeout for each wait attempt, in seconds
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

                    store_location = driver.find_element(By.CLASS_NAME,'store-location__location').text
                    if 'Gudang Blibli' in store_location:
                        store_location = driver.find_element(By.CLASS_NAME, 'store-location__warehouse-info-label').text

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
                        'store_location' : store_location,
                        "specifications" : specifications_dict,
                        "description" : description_text
                    }
                    page_end_time = time.time()
                    page_time = page_end_time - page_start_time
                    page_times.append(page_time) 

                    
                    
                    # logging.info(f"Page processed in {page_time:.2f} seconds")
                    # logging.info(json.dumps(product_dict, indent=4))
                    
                    all_product_in_page.append(product_dict)
                except (TimeoutException,NoSuchElementException) as e:
                    # with open("page_source.html", "w", encoding="utf-8") as f:
                    #     f.write(driver.page_source)
                    # driver.save_screenshot("debug_screenshot.png")
                    logging.warning(f"Detail product not showing up: {e}")
                    break

        if page_times:
            average_time = sum(page_times) / len(page_times)
            logging.info(f"Average time per page: {average_time:.2f} seconds for {len(page_times)} products")

        return all_product_in_page
    else:
        logging.info("No products found.")

def transform(product_list, keyword):
    for product in product_list:
        product['marketplace'] = 'Blibli'
        product['keyword'] = keyword
        product['selling_price'] = int(product['selling_price'].replace('Rp','').replace('.', ''))
        if product['original_price']:
            product['original_price'] = int(product['original_price'].replace('Rp','').replace('.', ''))
        if product['total_sold']:
            total_sold_str = product['total_sold'].replace('Terjual ', '')
            if 'rb' in total_sold_str:
                # Extract the numeric part, replace ',' with '.', and handle 'rb'
                numeric_part = total_sold_str.replace(' rb', '').replace(',', '.')
                product['total_sold'] = int(float(numeric_part) * 1000)
            else:
                product['total_sold'] = int(total_sold_str)
        
        if product['rating']:
            product['rating'] = float(product['rating'].replace(',','.'))
        if product['rating_count']:
            product['rating_count'] = int(product['rating_count'].replace('(','').replace(')',''))
    
    df = pd.DataFrame(product_list)
    df['specifications'] = df['specifications'].apply(json.dumps)
    return df

def get_db_connection():
    conn = {
        'login' : 'postgres',
        'password' : 'newpassword',
        'host' : '34.128.124.94',
        'port' : '5432',
        'schema' : 'postgres'
    }
    conn_url = f"postgresql+psycopg2://{conn['login']}:{conn['password']}@{conn['host']}:{conn['port']}/{conn['schema']}"
    return create_engine(conn_url)

def insert_new_rows_table(df, schema, table, index_row):
    engine = get_db_connection()
    connection = engine.connect()
    transaction = connection.begin()

    try:
        existing_index = pd.read_sql(f'SELECT {index_row} FROM {schema}.{table}', connection)
        # Check if existing_index is empty
        if existing_index.empty:
            logging.info(f"No existing rows found in {schema}.{table}. Proceeding to inject all rows.")
        else:
            # Filter the DataFrame based on existing indices
            df = df[~df[index_row].isin(existing_index[index_row])]

        # Check if DataFrame is empty after filtering
        if df.empty:
            logging.info(f"No new rows to inject into {schema}.{table}. DataFrame is empty after filtering.")
            return

        df.to_sql(table, connection, schema=schema, if_exists='append', index=False)
        transaction.commit()  # Commit only if no errors occurred
        logging.info(f"Injected {len(df)} rows into {schema}.{table}")

    except Exception as e:
        transaction.rollback()  # Rollback on error
        logging.error(f"Rolling back changes due to error: {str(e)}")
        raise
    finally:
        connection.close()

domain_url = "https://www.blibli.com/"
search_api = "cari/"
keyword = "Indomie Ayam Bawang 69 gr"
encoded_keyword = quote(keyword)
sort_bestseller = "?sort=16" # &intent=false
starting_url = domain_url + search_api + encoded_keyword + sort_bestseller

logging.info(f"Accessing {starting_url}")
driver.get(starting_url)

total_product = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "product-listing-totalItem"))
)
logging.info(f"Found {total_product.text}")

all_product_links = []  # Initialize product_links before the try block
css_selector = "div.product__card.product__card__five div.product__container a"
all_product_page = []
max_pagination = 2
current_pagination = 1
while current_pagination <= max_pagination:
    locator = (By.CSS_SELECTOR, '.blu-paging__link.is-current')
    text = str(current_pagination)
    try:
        WebDriverWait(driver, 10).until(
            element_to_be_clickable_with_text(locator, text)
        )
        logging.info(f"Moved to pagination {text}")
    except TimeoutException:
        logging.info(f"Timeout move to pagination {text}")
        try:
            driver.find_element((By.CLASS_NAME, 'list-pagination'))
        except NoSuchElementException:
            logging.info("No pagination option")
            break

    try:
        product_links = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector))
        )
        hrefs = [link.get_attribute("href") for link in product_links]
        all_product_links.extend(hrefs)
    except TimeoutException as e:
        logging.warning("Timeout waiting for product links: " + str(e))
    except Exception as e:
        logging.warning("General exception occurred: " + str(e))

    next_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'blu-paging__next'))
    )
    try:
        # Try clicking normally
        next_button.click()
    except ElementClickInterceptedException:
        # If normal click fails, use JavaScript click
        driver.execute_script("arguments[0].click();", next_button)
    current_pagination += 1


all_product_page = extract_product(driver, all_product_links)
clean_product_page = transform(all_product_page, keyword)
insert_new_rows_table(clean_product_page, 'external', 'product_competitor', 'sku_code')

# logging.info(clean_product_page.head())
# logging.info(clean_product_page.info())
# filename = keyword.replace(" ", "_") + ".json"
# with open(filename, 'w', encoding='utf-8') as f:
#     json.dump(product_page, f, indent=4)

driver.quit()
