import os
import cv2
import time
import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from selenium import webdriver
from sklearn.cluster import KMeans
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import re # Importăm modulul pentru expresii regulate
from selenium.webdriver.chrome.options import Options

# --- DATE AUTENTIFICARE ---
email = ""
password = ""

# --- CONFIGURARE ---
BASE_URL = "https://ralexpucioasa.ro/categorie-produs/lenjerii-de-pat/lenjerii-de-pat-policoton/lenjerii-finet-6-piese-cu-husa-pentru-saltea/page/"
SAVE_FOLDER = "imagini_paturi"
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

# Setări Selenium
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)
driver.get("https://ralexpucioasa.ro/")

def get_clean_image_url(url):
    """
    Transformă: ".../nume-poza-150x150.jpg"
    În:         ".../nume-poza.jpg"
    """
    if not url: return None
    # Căutăm tiparul "-cifraxCifra" înainte de extensia fișierului
    # Ex: -150x150, -300x300, -100x100
    clean_url = re.sub(r'-\d+x\d+(?=\.[a-zA-Z]+$)', '', url)
    return clean_url

def exec_login():
    try:
        driver.get("https://ralexpucioasa.ro/contul-meu/")
        time.sleep(1)

        consent_button = driver.find_element(By.CLASS_NAME, "fc-cta-consent")
        email_input = driver.find_element(By.ID, "username")
        password_input = driver.find_element(By.ID, "password")
        button_login = driver.find_element(By.NAME, "login")

        consent_button.click()
        email_input.send_keys(email)
        password_input.send_keys(password)
        button_login.click()

        time.sleep(1)

        return True
    except Exception as e:
        print(f"Eroare la autentificare: {e}")
        return False

def get_dominant_color(image_path, k=1):
    """
    Analizează imaginea și returnează culoarea dominantă sub formă de HEX.
    k=1 înseamnă că extragem doar cea mai importantă culoare.
    """
    try:
        image = cv2.imread(image_path)
        if image is None: return "N/A"
        
        # Redimensionăm pentru viteză
        image = cv2.resize(image, (100, 100), interpolation=cv2.INTER_AREA)
        # Convertim din BGR (OpenCV default) în RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # Reshape imaginea într-o listă de pixeli
        pixels = image.reshape((-1, 3))
        
        # Aplicăm K-Means pentru a găsi clusterele de culori
        kmeans = KMeans(n_clusters=k, n_init=10)
        kmeans.fit(pixels)
        
        # Luăm centrul clusterului (culoarea medie dominantă)
        dominant_color = kmeans.cluster_centers_[0].astype(int)
        
        # Convertim în format HEX (#RRGGBB)
        return '#{:02x}{:02x}{:02x}'.format(dominant_color[0], dominant_color[1], dominant_color[2])
    except Exception as e:
        return f"Eroare: {str(e)}"

def scrape_product_details(url):
    driver.get(url)
    time.sleep(1.5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    data = {}
    
    # 1. Titlu
    title_tag = soup.find('h1', class_='product_title')
    data['Titlu'] = title_tag.text.strip() if title_tag else "N/A"
    
    # --- LISTA DE IMAGINI ---
    image_links = []
    
    # A. Căutăm Imaginea Principală (zoomImg - de obicei e deja mare)
    main_img = soup.find('img', class_='zoomImg')
    if main_img and main_img.get('src'):
        image_links.append(main_img['src'])
        
    # B. Căutăm Imagini Secundare (Thumbnails) și extragem din SRCSET
    # Căutăm orice imagine care are clase de tip "attachment-..." și "size-..."
    thumbnails = soup.find_all('img', class_=re.compile(r'attachment-.*size-.*'))
    
    for thumb in thumbnails:
        # Pasul 1: Verificăm dacă are srcset (lista cu toate mărimile)
        srcset = thumb.get('srcset')
        
        if srcset:
            # Exemplu srcset: "link1 150w, link2 300w, link7 1760w"
            # Spargem șirul după virgulă
            parts = srcset.split(',')
            
            # Luăm ULTIMA parte (cea mai mare rezoluție)
            last_part = parts[-1].strip() # ex: "link7 1760w"
            
            # Spargem după spațiu pentru a separa linkul de lățime (1760w)
            high_res_url = last_part.split(' ')[0]
            
            if high_res_url not in image_links:
                image_links.append(high_res_url)
        
        else:
            # Fallback: Dacă nu există srcset, luăm src-ul și încercăm să-l curățăm
            raw_src = thumb.get('src')
            if raw_src:
                clean_url = get_clean_image_url(raw_src) # Funcția veche de backup
                if clean_url not in image_links:
                    image_links.append(clean_url)
    
    # --- EXPORT SI DOWNLOAD ---
    
    # Salvăm linkurile în Excel
    data['Link_Img_1'] = image_links[0] if len(image_links) > 0 else "N/A"
    data['Link_Img_2'] = image_links[1] if len(image_links) > 1 else "N/A"
    data['Link_Img_3'] = image_links[2] if len(image_links) > 2 else "N/A"

    # Downloadăm imaginile găsite (Max 3 de exemplu)
    for i, link in enumerate(image_links[:3]): 
        try:
            # Curățăm titlul pentru a crea un nume de fișier valid
            clean_title = "".join([c for c in data['Titlu'] if c.isalnum() or c in (' ', '-', '_')]).strip()
            # Adăugăm indexul la final (ex: Lenjerie_img1.jpg, Lenjerie_img2.jpg)
            filename = f"{clean_title}_img{i+1}.jpg"
            save_path = os.path.join(SAVE_FOLDER, filename)
            
            # Salvăm calea în Excel
            data[f'Path_Local_{i+1}'] = save_path
            
            # Descărcarea efectivă
            r = requests.get(link, stream=True)
            if r.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(r.content)
                
                # Opțional: Detectie culoare pentru prima imagine
                # if i == 0: data['Culoare_Detectata'] = get_dominant_color(save_path)
                
        except Exception as e:
            print(f"Eroare download imagine {i+1}: {e}")
            data[f'Path_Local_{i+1}'] = "Eroare"

    # --- Preț și alte detalii (neschimbat) ---
    wholesale_container = soup.find('span', class_='wholesale_price_container')
    if wholesale_container:
        ins_tag = wholesale_container.find('ins')
        data['Pret'] = ins_tag.get_text(strip=True) if ins_tag else wholesale_container.get_text(strip=True)
    else:
        price_p = soup.find('p', class_='price')
        if price_p:
            bdis = price_p.find_all('bdi')
            data['Pret'] = bdis[-1].get_text(strip=True) if bdis else "N/A"

    '''
    data['Dimensiuni'] = "N/A"
    data['Compozitie'] = "N/A"
    rows = soup.find_all('tr')
    for row in rows:
        text = row.get_text(separator=" ", strip=True)
        if "Dimensiuni:" in text:
            data['Dimensiuni'] = text.split("Dimensiuni:")[-1].strip()
        elif "Compoziție textilă:" in text:
            data['Compozitie'] = text.split("Compoziție textilă:")[-1].strip()
    '''
    return data

# --- FLUX PRINCIPAL ---
all_products_data = []

try:
    # Pasul 1: Logare
    if(not exec_login()):
        driver.get("https://ralexpucioasa.ro/contul-meu/")
        input("Te rugăm să te loghezi în browser, apoi apasă ENTER aici în consolă...")

    page_number = 1
    while True:
        print(f"Accesare pagina {page_number}...")
        driver.get(f"{BASE_URL}{page_number}/")
        
        # Verificăm dacă pagina există (dacă apare 404 sau nu sunt produse)
        if "404" in driver.title or page_number > 10: # Limită de siguranță
            break
            
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        links = soup.find_all('a', class_='product-image-link')
        
        if not links:
            break
            
        product_urls = [link['href'] for link in links]
        
        for url in product_urls:
            print(f"Scrapping produs: {url}")
            details = scrape_product_details(url)
            all_products_data.append(details)
            time.sleep(1) # Delay politicos
            
        page_number += 1

finally:
    # Salvare în Excel
    df = pd.DataFrame(all_products_data)
    df.to_excel("produse_ralex.xlsx", index=False)
    print("Export finalizat în produse_ralex.xlsx")
    driver.quit()
