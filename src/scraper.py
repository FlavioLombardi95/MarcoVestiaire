"""
Vestiaire Collective Scraper
Modulo per estrarre dati dai profili Vendors
"""

import time
import logging
from typing import Dict, List, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import re

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VestiaireScraper:
    """Classe per lo scraping dei profili Vestiaire Collective"""
    
    def __init__(self):
        self.driver = None
        self.profiles = {
            "Rediscover": "2039815",
            "Volodymyr": "5924329", 
            "stephanie": "9168643",
            "Mark": "13442939",
            "A Retro Tale": "5537180",
            "Lapsa": "11345596",
            "Bag": "3770739",
            "Clara": "27862876",
            "Baggy Vintage": "18106856",
            "Vintageandkickz": "19199976",
            "Vintage & Modern": "29517320"
        }
    
    def setup_driver(self):
        """Configura il driver Chrome per lo scraping"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Driver Chrome configurato con successo")
            
        except Exception as e:
            logger.error(f"Errore nella configurazione del driver: {e}")
            raise
    
    def extract_numbers_from_text(self, text: str) -> int:
        """Estrae numeri da una stringa di testo"""
        if not text:
            return 0
        
        # Cerca numeri nel testo (anche con separatori come punti e virgole)
        numbers = re.findall(r'[\d,\.]+', text.replace(' ', ''))
        if numbers:
            # Prendi il primo numero e rimuovi separatori
            number_str = numbers[0].replace(',', '').replace('.', '')
            try:
                return int(number_str)
            except ValueError:
                return 0
        return 0
    
    def scrape_profile(self, profile_name: str, profile_id: str) -> Dict:
        """Scrapa un singolo profilo Vestiaire"""
        url = f"https://it.vestiairecollective.com/profile/{profile_id}/?sortBy=relevance&tab=items-for-sale"
        
        try:
            logger.info(f"Scraping profilo: {profile_name} ({profile_id})")
            self.driver.get(url)
            
            # Attendi il caricamento della pagina
            time.sleep(5)
            
            # Cerca gli elementi con i dati
            articles = 0
            sales = 0
            
            # Prova diversi selettori per trovare i numeri
            selectors = [
                "//span[contains(text(), 'articoli') or contains(text(), 'items')]",
                "//div[contains(@class, 'count')]",
                "//span[contains(@class, 'number')]",
                "//div[contains(text(), 'articoli')]",
                "//span[contains(text(), 'vendite') or contains(text(), 'sales')]"
            ]
            
            page_source = self.driver.page_source
            
            # Cerca pattern comuni per articoli e vendite
            # Pattern per articoli
            article_patterns = [
                r'(\d+(?:,\d+)*)\s*articoli?',
                r'(\d+(?:,\d+)*)\s*items?',
                r'(\d+(?:,\d+)*)\s*prodotti?'
            ]
            
            # Pattern per vendite
            sales_patterns = [
                r'(\d+(?:,\d+)*)\s*vendite?',
                r'(\d+(?:,\d+)*)\s*sales?',
                r'(\d+(?:,\d+)*)\s*acquisti?'
            ]
            
            # Estrai articoli
            for pattern in article_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    articles = self.extract_numbers_from_text(matches[0])
                    break
            
            # Estrai vendite
            for pattern in sales_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    sales = self.extract_numbers_from_text(matches[0])
                    break
            
            # Se non troviamo i dati, prova a cercare elementi specifici
            if articles == 0 or sales == 0:
                try:
                    # Cerca elementi con classi specifiche
                    elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='count'], [class*='number'], [class*='stats']")
                    for element in elements:
                        text = element.text.lower()
                        if 'articoli' in text or 'items' in text:
                            articles = self.extract_numbers_from_text(element.text)
                        elif 'vendite' in text or 'sales' in text:
                            sales = self.extract_numbers_from_text(element.text)
                except Exception as e:
                    logger.warning(f"Errore nell'estrazione dati specifici per {profile_name}: {e}")
            
            logger.info(f"Profilo {profile_name}: {articles} articoli, {sales} vendite")
            
            return {
                "name": profile_name,
                "profile_id": profile_id,
                "url": url,
                "articles": articles,
                "sales": sales,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"Errore nello scraping del profilo {profile_name}: {e}")
            return {
                "name": profile_name,
                "profile_id": profile_id,
                "url": url,
                "articles": 0,
                "sales": 0,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e)
            }
    
    def scrape_all_profiles(self) -> List[Dict]:
        """Scrapa tutti i profili configurati"""
        if not self.driver:
            self.setup_driver()
        
        results = []
        
        try:
            for profile_name, profile_id in self.profiles.items():
                result = self.scrape_profile(profile_name, profile_id)
                results.append(result)
                
                # Pausa tra le richieste per evitare rate limiting
                time.sleep(3)
                
        except Exception as e:
            logger.error(f"Errore generale nello scraping: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Driver Chrome chiuso")
        
        return results
    
    def calculate_totals(self, results: List[Dict]) -> Dict:
        """Calcola i totali degli articoli e vendite"""
        total_articles = sum(result.get('articles', 0) for result in results)
        total_sales = sum(result.get('sales', 0) for result in results)
        
        return {
            "total_articles": total_articles,
            "total_sales": total_sales,
            "profiles_count": len(results)
        }

def main():
    """Funzione principale per testare lo scraper"""
    scraper = VestiaireScraper()
    results = scraper.scrape_all_profiles()
    
    print("=== RISULTATI SCRAPING ===")
    for result in results:
        print(f"{result['name']}: {result['articles']} articoli, {result['sales']} vendite")
    
    totals = scraper.calculate_totals(results)
    print(f"\nTOTALI: {totals['total_articles']} articoli, {totals['total_sales']} vendite")

if __name__ == "__main__":
    main() 