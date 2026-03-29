import re

import cv2
from sklearn.cluster import KMeans

from scraper_interface import *

class RalexScraper(IScraper):
    def __init__(self):
        self.data = []
        self.email, self.password = read_login_credentials("ralex_login.txt")

    def exec_login(self):
        try:
            self.driver.get("https://ralexpucioasa.ro/contul-meu/")
            time.sleep(0.1)

            consent_button = self.driver.find_element(By.CLASS_NAME, "fc-cta-consent")
            email_input = self.driver.find_element(By.ID, "username")
            password_input = self.driver.find_element(By.ID, "password")
            button_login = self.driver.find_element(By.NAME, "login")

            consent_button.click()
            email_input.send_keys(self.email)
            password_input.send_keys(self.password)
            button_login.click()

            time.sleep(0.5)

            return True
        except Exception as e:
            print(f"Eroare la autentificare: {e}")
            return False
        
    def process(self, url):
        super().__init__()

        if(not self.exec_login()):
            self.driver.get("https://ralexpucioasa.ro/contul-meu/")
            input("Te rugăm să te loghezi în browser, apoi apasă ENTER aici în consolă...")

        page_number = 1
        while True:
            print(f"Accesare pagina {page_number}...")
            self.driver.get(f"{url}/page/{page_number}/")
            self.soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            if page_number > MAX_PAGE_COUNT:
                print("Limit Reached. Stopping scraper.")
                break
            
            links = self.soup.find_all('a', class_='product-image-link')

            if self.soup.find('head') is not None:
                if self.soup.find('head').find('title') is not None:
                    title = self.soup.find('head').find('title').text.strip()
                    if title == "Pagină negăsită":
                        print("Page not found. Stopping scraper.")
                        break
            
            if not links:
                print("No links found. Stopping scraper.")
                break
                
            product_urls = [link['href'] for link in links]
            
            for url in product_urls:
                print(f"Scrapping produs: {url}")
                details = self.scrape(url)
                self.data.append(details)
                
            page_number += 1

    def scrape(self, url):
        super().scrape(url)

        details = {}

        # 1. Scrape title
        details['TITLE'] = self.scrape_product_title()
        # 2. Scrape price
        details['PRICE'] = self.scrape_product_price()
        # 3. Scrape images
        for i, image in enumerate(self.scrape_product_images()):
            image = image.split("&width")[0]  # Remove query parameters
            details[f'IMAGE_{i}'] = image
        # 4. Scrape description
        #details['DESCRIPTION'] = self.scrape_product_description()
        # 5. Scrape variations
        for key, value in self.scrape_product_variations().items():
            details[key] = value
        # 6. Scrape characteristics
        for key, value in self.scrape_product_characteristics().items():
            details[key] = value

        return details
    
    def scrape_product_title(self):
        title_tag = self.soup.find('h1', class_='product_title')
        return  title_tag.text.strip() if title_tag else "N/A"
    
    def scrape_product_price(self):
        wholesale_container = self.soup.find('span', class_='wholesale_price_container')
        if wholesale_container:
            ins_tag = wholesale_container.find('ins')
            return ins_tag.get_text(strip=True) if ins_tag else wholesale_container.get_text(strip=True)
        else:
            price_p = self.soup.find('p', class_='price')
            if price_p:
                bdis = price_p.find_all('bdi')
                return bdis[-1].get_text(strip=True) if bdis else "N/A"
            
    def scrape_product_images(self):
        images = []

        if self.soup.find('div', class_='wd-carousel-wrap') is not None:
            image_tags = self.soup.find('div', class_='wd-carousel-wrap').find_all('img')
            for img in image_tags:
                if img.has_attr('src'):
                    clean_url = get_clean_image_url(img['src']).split("150x150")[0]
                    if clean_url:
                        images.append(clean_url)
        else:
            image_tag =self.soup.find(img, role='presentation')
            if image_tag and image_tag.has_attr('src'):
                clean_url = get_clean_image_url(image_tag['src']).split("150x150")[0]
                if clean_url:
                    images.append(clean_url)
        return images
    
    def scrape_product_variations(self):
        variations = {}
        variation_key = None

        if self.soup.find('table', class_='variations') is not None:
            variation_rows = self.soup.find('table', class_='variations').find_all('tr')
            for row in variation_rows:
                header = row.find('th').find('label')
                value = row.find('td').find_all('option')

                if header == None and value == None:
                    continue

                variation_key = header.text.strip()

                for option in value:
                    if option.has_attr('value') and option['value'] != "":
                        variations[variation_key] = option['value']

        return variations
    
    def scrape_product_characteristics(self):
        characteristics = {}

        if self.soup.find('div', class_='woocommerce-product-details__short-description') is not None:
            description_div = self.soup.find('div', class_='woocommerce-product-details__short-description')
            if description_div.find('table') is not None:
                rows = description_div.find('table').find('tbody').find_all('tr')
                for row in rows:
                    key = None
                    value = None
                    for cell in row.find_all('td'):
                        if cell.find('b') is not None:
                            key = cell.find('b').text.strip()
                        elif cell.find('span') is not None:
                            value = cell.text.strip()
                    if key and value:
                        characteristics[key] = value

        return characteristics