import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

MAX_PAGE_COUNT = 10

def get_clean_image_url(url):
        if not url: 
            return None
        
        clean_url = re.sub(r'-\d+x\d+(?=\.[a-zA-Z]+$)', '', url)
        return clean_url

def read_login_credentials(filename):
    try:
        with open(filename, "r") as file:
            email = file.readline().strip()
            password = file.readline().strip()
            return email, password
    except Exception as e:
        print(f"Error reading login credentials: {e}")
        return None, None

class IScraper:

    def __init__(self):
        self.data = []
        self.options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(options=self.options)

    # this method will be called by the user, it will sort out the scraping process
    def process(self, url):
        raise NotImplementedError("Subclasses must implement this method 'process'")

    def scrape(self, url):
        self.driver.get(url)
        time.sleep(0.5) # Wait for the page to load
        self.soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        #raise NotImplementedError("Subclasses must implement this method 'scrape'")
    
    def scrape_product_title(self) -> str:
        raise NotImplementedError("Subclasses must implement this method 'scrape_product_title'")
    
    def scrape_product_price(self) -> float:
        raise NotImplementedError("Subclasses must implement this method 'scrape_product_price'")
    
    def scrape_product_images(self) -> list:
        raise NotImplementedError("Subclasses must implement this method 'scrape_product_images'")
    
    def scrape_product_description(self) -> str:
        raise NotImplementedError("Subclasses must implement this method 'scrape_product_description'")

    def scrape_product_variations(self) -> dict:
        raise NotImplementedError("Subclasses must implement this method 'scrape_product_variations'")
    
    def scrape_product_characteristics(self) -> dict:
        raise NotImplementedError("Subclasses must implement this method 'scrape_product_characteristics'")

    def save_to_excel(self, data, save_name):
        import pandas as pd
        df = pd.DataFrame(data)
        df.to_excel(f"saved/{save_name}.xlsx", index=False)
        print(f"Data saved to {save_name}.xlsx")

    def close(self):
        self.driver.quit()