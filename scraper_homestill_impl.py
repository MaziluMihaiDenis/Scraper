from scraper_interface import *

class HomestillScraper(IScraper):

    def __init__(self):
        self.data = []

    def process(self, url):
        super().__init__()

        page_number = 1
        while True:
            print(f"Accesare pagina {page_number}...")
            self.driver.get(f"{url}?page={page_number}")
            self.soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            if page_number > MAX_PAGE_COUNT: 
                print("Limit Reached. Stopping scraper.")
                break

            if self.soup.find('h2', class_='title title--primary') is not None:
                print("No more products found. Stopping scraper.")
                break

            links = self.soup.find_all('a', class_='full-unstyled-link')

            for i in range(len(links) - 1, -1, -1):
                if links[i]['aria-labelledby'].__contains__("StandardCardNoMediaLink"):
                    del links[i]

            for link in links:
                product_url = link['href']
                product_details = self.scrape(f"{url}{product_url}")
                print(f"Scrapping produs: {product_url}")
                self.data.append(product_details)
        
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
        #for key, value in self.scrape_product_variations().items():
        #    details[key] = value
        # 6. Scrape characteristics
        for key, value in self.scrape_product_characteristics().items():
            details[key] = value

        return details

    def scrape_product_title(self) -> str:
        title_tag = self.soup.find('h1', class_='h2')
        return title_tag.text.strip() if title_tag else "N/A"
    
    def scrape_product_price(self) -> float:
        price_tag = self.soup.find('span', class_='price-item--regular')
        if price_tag:
            price_text = price_tag.text.strip()
            # Remove currency symbol and convert to float
            price_text = price_text.replace('lei', '').replace('.', '').replace(',', '.').strip()
            try:
                return float(price_text)
            except ValueError:
                return 0.0
        return 0.0
    
    def scrape_product_images(self) -> list:
        images = []

        if self.soup.find('ul', class_='thumbnail-list') is None:
            if self.soup.find('div', class_='product__media') is not None:
                img_tag = self.soup.find('div', class_='product__media').find('img')
                if img_tag and 'src' in img_tag.attrs:
                    images.append(img_tag['src'])
            return images
        for children in self.soup.find('ul', class_='thumbnail-list').children:
            if children.name == 'li':
                img_tag = children.find('button').find('img') if children.find('button') else None
                if img_tag and 'src' in img_tag.attrs:
                    images.append(img_tag['src'])
        return images
    
    def scrape_product_description(self) -> str:
        description_tag = self.soup.find('div', class_='product__description')
        return description_tag.text.strip() if description_tag else "N/A"
    
    def scrape_product_variations(self) -> dict:
        variations = {}
        variations_list = []
        variation_key = None

        if self.soup.find('div', class_='product-form__label-container') is not None:
            variation_span = self.soup.find('div', class_='product-form__label-container').find('span')
            if variation_span and variation_span.text.strip() != None:
                variation_key = variation_span.text.strip().split(" ")[0]

        if self.soup.find('div', class_='color-swatches-container') is not None:
            if self.soup.find_all('div', class_='color-swatch') is not None:
                for variation in self.soup.find_all('div', class_='color-swatch'):
                    if variation.find('span', class_='color-swatch__label') is not None:
                        variation_text = variation.find('span', class_='color-swatch__label').text.strip()
                    variations_list.append(variation_text)
                if variation_key and variations_list:
                    variations[variation_key.upper()] = variations_list

        return variations
    
    def scrape_product_characteristics(self) -> dict:
        characteristics = {}
        if self.soup.find('table') is not None:
            for detail in self.soup.find('table').find_all('tr'):
                if detail.find_all('td'):
                    key = detail.find_all('td')[0].text.strip().upper()
                    value = detail.find_all('td')[1].text.strip()
                    characteristics[key] = value

        return characteristics
