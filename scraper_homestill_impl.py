from scraper_interface import *

class HomestillScraper(IScraper):

    def process(self, url):
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
        details['title'] = self.scrape_product_title()
        # 2. Scrape price
        details['price'] = self.scrape_product_price()
        # 3. Scrape images
        for i, image in enumerate(self.scrape_product_images()):
            image = image.split("&width")[0]  # Remove query parameters
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