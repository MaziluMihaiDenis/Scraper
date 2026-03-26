from scraper_interface import *

class HomestillScraper(IScraper):

    def process(self, url):
        page_number = 1
        while True:
            print(f"Accesare pagina {page_number}...")
            self.driver.get(f"{url}?page={page_number}")
        
            if "404" in self.driver.title or page_number > MAX_PAGE_COUNT: 
                print("No more pages to scrape or reached")
                break

            self.soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            links = self.soup.find_all('a', class_='full-unstyled-link')

            for link in links:
                product_url = link['href']
                product_details = self.scrape(f"{url}{product_url}")
                print(f"Scrapping produs: {product_url}")
                self.data.append(product_details)
                time.sleep(1) # Delay
        
            page_number += 1

    def scrape(self, url):
        super().scrape(url)

        print("Scraping homestill.ro...")

        details = {}

        # 1. Scrape title
        details['title'] = self.scrape_product_title()
        # 2. Scrape price
        details['price'] = self.scrape_product_price()
        # 3. Scrape images
        for i, image in enumerate(self.scrape_product_images()):
            details[f'image_{i}'] = image
        # 4. Scrape description
        details['description'] = self.scrape_product_description()

        return details

    def scrape_product_title(self) -> str:
        title_tag = self.soup.find('h1', class_='h2')
        return title_tag.text.strip() if title_tag else "N/A"
    
    def scrape_product_price(self) -> float:
        price_tag = self.soup.find('span', class_='price-item--regular')
        if price_tag:
            price_text = price_tag.text.strip()
            # Remove currency symbol and convert to float
            price_text = price_text.replace('lei', '').replace(',', '.').strip()
            try:
                return float(price_text)
            except ValueError:
                return 0.0
        return 0.0
    
    def scrape_product_images(self) -> list:
        images = []
        for children in self.soup.find('ul', class_='thumbnail-list').children:
            if children.name == 'li':
                img_tag = children.find('button').find('img') if children.find('button') else None
                if img_tag and 'src' in img_tag[0].attrs:
                    images.append(img_tag[0]['src'])
        return images