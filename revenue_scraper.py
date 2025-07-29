"""
Revenue Scraper - Scraper parallelo per analisi ricavi
Modulo per estrarre prezzi degli articoli venduti dai profili Vestiaire Collective
"""

import time
import logging
import re
from typing import Dict, List, Tuple
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RevenueScraper:
    """Classe per lo scraping dei prezzi degli articoli venduti"""
    
    def __init__(self, profiles=None, existing_sales_data=None):
        self.driver = None
        # Usa la configurazione esterna se fornita, altrimenti usa quella di default
        if profiles:
            self.profiles = profiles
        else:
            # Importa la configurazione da config.py
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from config import VESTIAIRE_PROFILES
            self.profiles = VESTIAIRE_PROFILES
        
        # Dati vendite esistenti dal sistema principale
        self.existing_sales_data = existing_sales_data or {}
        
        # Statistiche performance
        self.performance_stats = {
            "driver_setup_time": 0,
            "total_scraping_time": 0,
            "profile_times": {},
            "average_profile_time": 0,
            "fastest_profile": {"name": "", "time": float('inf')},
            "slowest_profile": {"name": "", "time": 0}
        }
    
    def setup_driver(self):
        """Configura il driver Chrome per lo scraping"""
        start_time = time.time()
        try:
            logger.info("⏱️ Configurazione driver Chrome per revenue scraping...")
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            # Gestione specifica per macOS
            import platform
            if platform.system() == "Darwin":
                chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Ottieni il percorso del ChromeDriver
            driver_path = ChromeDriverManager().install()
            if driver_path.endswith('THIRD_PARTY_NOTICES.chromedriver'):
                driver_path = driver_path.replace('THIRD_PARTY_NOTICES.chromedriver', 'chromedriver')
            
            # Fix permessi per GitHub Actions (Linux)
            if platform.system() == "Linux":
                import stat
                import os
                try:
                    os.chmod(driver_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)
                    logger.info(f"🔧 Permessi chromedriver impostati: {driver_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Impossibile impostare permessi chromedriver: {e}")
            
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            setup_time = time.time() - start_time
            self.performance_stats["driver_setup_time"] = setup_time
            logger.info(f"✅ Driver Chrome configurato in {setup_time:.2f} secondi")
            
        except Exception as e:
            logger.error(f"Errore nella configurazione del driver: {e}")
            raise
    
    def extract_price_from_text(self, text: str) -> float:
        """Estrae il prezzo da una stringa di testo"""
        if not text:
            return 0.0
        
        # Cerca pattern di prezzo (es. €150, €1,500, 150€, etc.)
        price_patterns = [
            r'€\s*([\d,\.]+)',  # €150, €1,500
            r'([\d,\.]+)\s*€',  # 150€, 1,500€
            r'([\d,\.]+)\s*EUR', # 150 EUR
            r'EUR\s*([\d,\.]+)', # EUR 150
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text.replace(' ', ''))
            if match:
                try:
                    # Rimuovi separatori e converti in float
                    price_str = match.group(1).replace(',', '').replace('.', '')
                    return float(price_str)
                except ValueError:
                    continue
        
        return 0.0
    
    def scrape_profile_revenue(self, profile_name: str, profile_id: str) -> Dict:
        """Scrapa i prezzi degli articoli venduti per un singolo profilo"""
        # Prima accediamo alla pagina normale del profilo
        url = f"https://it.vestiairecollective.com/profile/{profile_id}/"
        
        profile_start_time = time.time()
        sold_items_prices = []
        total_revenue = 0.0
        
        try:
            logger.info(f"💰 Scraping ricavi profilo: {profile_name} ({profile_id})")
            
            # Misurazione tempo di caricamento pagina
            page_load_start = time.time()
            self.driver.get(url)
            
            # Attendi il caricamento della pagina
            time.sleep(5)
            page_load_time = time.time() - page_load_start
            
            # Verifica se la pagina è caricata correttamente
            page_title = self.driver.title
            if "403" in page_title or "404" in page_title or "error" in page_title.lower():
                logger.error(f"❌ Pagina di errore rilevata per {profile_name}: {page_title}")
                raise Exception(f"Pagina di errore: {page_title}")
            
            # Misurazione tempo di parsing
            parse_start = time.time()
            
            # Ora cerchiamo il tab "sold" o "venduti" e clicchiamo su di esso
            logger.debug(f"  📍 Cercando tab sold/venduti per {profile_name}")
            
            # Cerca il tab "sold" o "venduti" e cliccalo
            sold_tab_found = False
            sold_tab_selectors = [
                "//a[contains(text(), 'sold') or contains(text(), 'venduti')]",
                "//button[contains(text(), 'sold') or contains(text(), 'venduti')]",
                "//div[contains(text(), 'sold') or contains(text(), 'venduti')]",
                "//span[contains(text(), 'sold') or contains(text(), 'venduti')]",
                "//a[contains(@href, 'sold') or contains(@href, 'venduti')]",
                "//a[contains(@class, 'sold') or contains(@class, 'venduti')]"
            ]
            
            for selector in sold_tab_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        try:
                            # Verifica che sia cliccabile e visibile
                            if element.is_displayed() and element.is_enabled():
                                element.click()
                                time.sleep(3)  # Attendi caricamento
                                sold_tab_found = True
                                logger.debug(f"  ✅ Tab sold trovato e cliccato con selettore: {selector}")
                                break
                        except Exception as e:
                            continue
                    if sold_tab_found:
                        break
                except Exception:
                    continue
            
            if not sold_tab_found:
                logger.warning(f"  ⚠️ Tab sold non trovato per {profile_name}, continuo con la pagina corrente")
            
            # Cerca tutti gli elementi che potrebbero contenere prezzi nella sezione sold
            price_elements = []
            
            # Cerca in diversi tipi di elementi specifici per items-for-sale
            selectors = [
                "//span[contains(@class, 'price') or contains(@class, 'Price')]",
                "//div[contains(@class, 'price') or contains(@class, 'Price')]",
                "//span[contains(@class, 'item-price')]",
                "//div[contains(@class, 'item-price')]",
                "//span[contains(text(), '€')]",
                "//div[contains(text(), '€')]",
                "//span[contains(text(), 'EUR')]",
                "//div[contains(text(), 'EUR')]",
                "//div[contains(@class, 'product-card')]//span[contains(text(), '€')]",
                "//div[contains(@class, 'product-card')]//div[contains(text(), '€')]"
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    price_elements.extend(elements)
                except Exception:
                    continue
            
            # Estrai prezzi dagli elementi trovati
            for element in price_elements:
                try:
                    text = element.text.strip()
                    if text:
                        price = self.extract_price_from_text(text)
                        if price > 0:
                            sold_items_prices.append(price)
                            logger.debug(f"  💰 Prezzo trovato: €{price}")
                except Exception as e:
                    logger.debug(f"  ⚠️ Errore estrazione prezzo: {e}")
            
            # Se non abbiamo trovato prezzi, prova a cercare in tutto il contenuto della pagina
            if not sold_items_prices:
                logger.debug(f"  🔍 Ricerca prezzi nel contenuto completo per {profile_name}")
                page_text = self.driver.page_source
                
                # Cerca pattern di prezzi nel testo della pagina
                price_matches = re.findall(r'€\s*([\d,\.]+)|([\d,\.]+)\s*€', page_text)
                for match in price_matches:
                    price_str = match[0] if match[0] else match[1]
                    if price_str:
                        try:
                            price = float(price_str.replace(',', '').replace('.', ''))
                            if price > 0 and price < 10000:  # Filtra prezzi ragionevoli
                                sold_items_prices.append(price)
                        except ValueError:
                            continue
            
            # Ora otteniamo il numero reale di articoli venduti dai dati esistenti
            real_sold_count = 0
            
            # Cerca nei dati esistenti dal sistema principale
            if profile_name in self.existing_sales_data:
                real_sold_count = self.existing_sales_data[profile_name].get('sales', 0)
                logger.info(f"  📊 Usando dati esistenti: {real_sold_count} vendite reali per {profile_name}")
            else:
                # Fallback: cerca nella pagina per il numero di vendite totali
                sold_count_selectors = [
                    "//span[contains(text(), 'venduti')]",
                    "//div[contains(text(), 'venduti')]",
                    "//span[contains(text(), 'sold')]",
                    "//div[contains(text(), 'sold')]"
                ]
                
                for selector in sold_count_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            text = element.text.strip()
                            if text:
                                # Estrai il numero di vendite dal testo
                                import re
                                numbers = re.findall(r'\d+', text)
                                if numbers:
                                    # Cerca il numero più grande che potrebbe essere il totale vendite
                                    potential_counts = [int(n) for n in numbers if int(n) > 0 and int(n) < 100000]
                                    if potential_counts:
                                        # Prendi il numero più grande che sembra essere il totale
                                        real_sold_count = max(potential_counts)
                                        logger.info(f"  📊 Trovato numero vendite: {real_sold_count} da testo: '{text}'")
                                        break
                        if real_sold_count > 0:
                            break
                    except Exception:
                        continue
            
            # Se non abbiamo trovato il numero reale, stimiamo basandomi sui prezzi estratti
            if real_sold_count == 0:
                # Stima: se abbiamo molti prezzi, probabilmente sono tutti venduti
                # Se abbiamo pochi prezzi, potrebbero essere solo quelli visibili
                if len(sold_items_prices) > 50:
                    # Molti prezzi = probabilmente tutti venduti
                    real_sold_count = len(sold_items_prices)
                    logger.info(f"  📊 Stima: {real_sold_count} vendite (basato su {len(sold_items_prices)} prezzi estratti)")
                else:
                    # Pochi prezzi = potrebbero essere solo quelli visibili
                    # Cerca di trovare il numero totale nella pagina
                    page_text = self.driver.page_source
                    import re
                    # Cerca pattern come "X venduti" o "X sold"
                    sold_patterns = [
                        r'(\d+)\s+venduti',
                        r'(\d+)\s+sold',
                        r'venduti\s+(\d+)',
                        r'sold\s+(\d+)'
                    ]
                    
                    for pattern in sold_patterns:
                        matches = re.findall(pattern, page_text, re.IGNORECASE)
                        if matches:
                            potential_count = int(matches[0])
                            if potential_count > len(sold_items_prices):
                                real_sold_count = potential_count
                                logger.info(f"  📊 Trovato totale vendite: {real_sold_count} (pattern: {pattern})")
                                break
                    
                    if real_sold_count == 0:
                        real_sold_count = len(sold_items_prices)
                        logger.warning(f"  ⚠️ Usando {real_sold_count} articoli estratti come stima per {profile_name}")
            
            # Calcola il fattore di correzione per i ricavi
            if real_sold_count > len(sold_items_prices):
                # Abbiamo più vendite totali che prezzi estratti
                # Calcola il prezzo medio e moltiplica per il totale
                if sold_items_prices:
                    avg_price = sum(sold_items_prices) / len(sold_items_prices)
                    estimated_revenue = avg_price * real_sold_count
                    logger.info(f"  📊 Stima ricavi: {len(sold_items_prices)} prezzi estratti, {real_sold_count} vendite totali")
                    logger.info(f"  📊 Prezzo medio: €{avg_price:.2f}, Ricavi stimati: €{estimated_revenue:.2f}")
                    total_revenue = estimated_revenue
                else:
                    total_revenue = 0
            else:
                # Usa i prezzi estratti direttamente
                total_revenue = sum(sold_items_prices)
            

            
            parse_time = time.time() - parse_start
            total_profile_time = time.time() - profile_start_time
            
            # Salva statistiche profilo
            self.performance_stats["profile_times"][profile_name] = {
                "total_time": total_profile_time,
                "page_load_time": page_load_time,
                "parse_time": parse_time,
                "items_found": len(sold_items_prices),
                "total_revenue": total_revenue,
                "data_found": len(sold_items_prices) > 0
            }
            
            # Aggiorna fastest/slowest
            if total_profile_time < self.performance_stats["fastest_profile"]["time"]:
                self.performance_stats["fastest_profile"] = {
                    "name": profile_name,
                    "time": total_profile_time
                }
            if total_profile_time > self.performance_stats["slowest_profile"]["time"]:
                self.performance_stats["slowest_profile"] = {
                    "name": profile_name,
                    "time": total_profile_time
                }
            
            logger.info(f"✅ {profile_name}: {len(sold_items_prices)} articoli venduti, €{total_revenue:.2f} ricavi (⏱️ {total_profile_time:.2f}s)")
            
            return {
                "name": profile_name,
                "profile_id": profile_id,
                "url": url,
                "sold_items_count": real_sold_count,
                "total_revenue": total_revenue,
                "sold_items_prices": sold_items_prices,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "success": True,
                "data_quality": {
                    "items_found": len(sold_items_prices) > 0,
                    "real_sold_count_found": real_sold_count > 0,
                    "page_title": page_title,
                    "price_elements_found": len(price_elements)
                },
                "performance": {
                    "total_time": total_profile_time,
                    "page_load_time": page_load_time,
                    "parse_time": parse_time
                }
            }
            
        except Exception as e:
            total_profile_time = time.time() - profile_start_time
            logger.error(f"❌ Errore nello scraping ricavi del profilo {profile_name}: {e}")
            return {
                "name": profile_name,
                "profile_id": profile_id,
                "url": url,
                "sold_items_count": 0,
                "total_revenue": 0.0,
                "sold_items_prices": [],
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "success": False,
                "error": str(e),
                "performance": {
                    "total_time": total_profile_time,
                    "page_load_time": 0,
                    "parse_time": 0
                }
            }
    
    def scrape_all_profiles_revenue(self) -> List[Dict]:
        """Scrapa i ricavi di tutti i profili configurati"""
        if not self.driver:
            self.setup_driver()
        
        results = []
        scraping_start_time = time.time()
        
        try:
            total_profiles = len(self.profiles)
            logger.info(f"🚀 Avvio scraping ricavi di {total_profiles} profili...")
            
            for i, (profile_name, profile_id) in enumerate(self.profiles.items(), 1):
                logger.info(f"📊 Progresso ricavi: {i}/{total_profiles}")
                
                result = self.scrape_profile_revenue(profile_name, profile_id)
                results.append(result)
                
                # Pausa tra le richieste per evitare rate limiting
                if i < total_profiles:
                    logger.info("⏳ Pausa 3 secondi...")
                    time.sleep(3)
                
        except Exception as e:
            logger.error(f"Errore generale nello scraping ricavi: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🔄 Driver Chrome chiuso")
        
        # Calcola statistiche finali
        total_scraping_time = time.time() - scraping_start_time
        self.performance_stats["total_scraping_time"] = total_scraping_time
        
        valid_times = [stats["total_time"] for stats in self.performance_stats["profile_times"].values()]
        if valid_times:
            self.performance_stats["average_profile_time"] = sum(valid_times) / len(valid_times)
        
        self._log_performance_summary()
        
        return results
    
    def _log_performance_summary(self):
        """Mostra un riassunto delle performance"""
        stats = self.performance_stats
        
        print("\n" + "="*60)
        print("💰 REPORT PERFORMANCE REVENUE SCRAPING")
        print("="*60)
        print(f"⏱️  Tempo setup driver: {stats['driver_setup_time']:.2f}s")
        print(f"⏱️  Tempo totale scraping: {stats['total_scraping_time']:.2f}s")
        print(f"⏱️  Tempo medio per profilo: {stats['average_profile_time']:.2f}s")
        print(f"🏆 Profilo più veloce: {stats['fastest_profile']['name']} ({stats['fastest_profile']['time']:.2f}s)")
        print(f"🐌 Profilo più lento: {stats['slowest_profile']['name']} ({stats['slowest_profile']['time']:.2f}s)")
        print(f"👥 Profili processati: {len(stats['profile_times'])}")
        
        print("\n📋 DETTAGLI PER PROFILO:")
        print("-" * 60)
        for name, data in stats["profile_times"].items():
            print(f"{name:20} | {data['total_time']:6.2f}s | Items: {data['items_found']:3d} | Revenue: €{data['total_revenue']:8.2f}")
        
        # Calcolo efficienza
        total_wait_time = (len(self.profiles) - 1) * 3
        active_work_time = stats['total_scraping_time'] - total_wait_time
        efficiency = (active_work_time / stats['total_scraping_time']) * 100 if stats['total_scraping_time'] > 0 else 0
        
        print(f"\n⚡ EFFICIENZA:")
        print(f"   Tempo di lavoro effettivo: {active_work_time:.2f}s")
        print(f"   Tempo di attesa totale: {total_wait_time:.2f}s")
        print(f"   Efficienza: {efficiency:.1f}%")
        print("="*60)
    
    def get_performance_stats(self) -> Dict:
        """Restituisce le statistiche di performance"""
        return self.performance_stats
    
    def calculate_revenue_totals(self, results: List[Dict]) -> Dict:
        """Calcola i totali dei ricavi"""
        total_items = sum(result.get('sold_items_count', 0) for result in results)
        total_revenue = sum(result.get('total_revenue', 0.0) for result in results)
        
        return {
            "total_sold_items": total_items,
            "total_revenue": total_revenue,
            "profiles_count": len(results)
        }

def main():
    """Funzione principale per testare lo scraper ricavi"""
    scraper = RevenueScraper()
    results = scraper.scrape_all_profiles_revenue()
    
    print("=== RISULTATI REVENUE SCRAPING ===")
    for result in results:
        print(f"{result['name']}: {result['sold_items_count']} articoli venduti, €{result['total_revenue']:.2f} ricavi")
    
    totals = scraper.calculate_revenue_totals(results)
    print(f"\nTOTALI: {totals['total_sold_items']} articoli venduti, €{totals['total_revenue']:.2f} ricavi totali")

if __name__ == "__main__":
    main() 