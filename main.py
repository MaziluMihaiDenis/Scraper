import threading

import customtkinter as ctk

from scraper_ralex_impl import RalexScraper
from scraper_homestill_impl import HomestillScraper

link_dict = {
    "ralexpucioasa": RalexScraper(),
    "homestill": HomestillScraper()
}

class InputBox(ctk.CTkEntry):
    def __init__(self, master=None, label_text="", **kwargs):
        super().__init__(master, **kwargs)
        self.Label = ctk.CTkLabel(master=master, text=label_text)
        self.Label.pack(pady=0)
        self.pack(pady=10)
        

class AppUserInterface(ctk.CTk):

    #Setting up the ui and the window
    def __init__(self):
        super().__init__()

        self._apply_appearance_mode("dark")
        self.title("Web Scraper")
        self.geometry("400x300")
        self.resizable(False, False)

        self.frame = ctk.CTkFrame(self)
        self.frame.pack(pady=50, padx=50, fill="both", expand=True)

        self.url_entry = InputBox(master=self.frame, label_text="Enter URL:", width=300)
        self.save_name_entry = InputBox(master=self.frame, label_text="File Name:", width=300)

        self.scrape_button = ctk.CTkButton(master=self.frame, text="Scrape", command=self.scrape)
        self.scrape_button.pack(pady=0)

        self.status_label = ctk.CTkLabel(master=self.frame, text="Status: Ready")
        self.status_label.pack(pady=0)

    def process_scraping(self, scraper_module, url, save_name):
        try:
            scraper_module.process(url)
            scraper_module.save_to_excel(scraper_module.data, save_name)
            scraper_module.close()
            self.status_label.configure(text="Scraping completed successfully!", fg_color="green")
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}", fg_color="red")
            print(f"Error at scraping: {e}")

    def scrape(self):
        url = self.url_entry.get()
        save_name = self.save_name_entry.get()

        for key in link_dict.keys():
            if url.__contains__(key):
                # Starting Scraper Module On A New Thread
                scraper_module = link_dict[key]
                threading.Thread(target=self.process_scraping, args=(scraper_module, url, save_name)).start()

                self.status_label.configure(text="Scraping... " + link_dict[key].__class__.__name__)
                self.mainloop() 

                return

        self.status_label.configure(text="Invalid URL!", fg_color="red")
        
user_interface = AppUserInterface()
user_interface.mainloop()