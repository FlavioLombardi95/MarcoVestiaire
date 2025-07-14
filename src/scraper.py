"""
Vestiaire Collective Scraper
Modulo per estrarre dati dai profili Vendors
"""

import time
import logging
from typing import Dict, List, Tuple
from datetime import datetime
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
            logger.info("⏱️ Configurazione driver Chrome in corso...")
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
                # Per macOS, usa il percorso diretto di Chrome
                chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Ottieni il percorso del ChromeDriver
            driver_path = ChromeDriverManager().install()
            # Assicurati che punti al file chromedriver corretto
            if driver_path.endswith('THIRD_PARTY_NOTICES.chromedriver'):
                driver_path = driver_path.replace('THIRD_PARTY_NOTICES.chromedriver', 'chromedriver')
            
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            setup_time = time.time() - start_time
            self.performance_stats["driver_setup_time"] = setup_time
            logger.info(f"✅ Driver Chrome configurato in {setup_time:.2f} secondi")
            
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
        
        profile_start_time = time.time()
        articles = 0
        sales = 0
        
        try:
            logger.info(f"🔍 Scraping profilo: {profile_name} ({profile_id})")
            
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
            
            # DEBUG: stampa tutti i testi di <span> e <div> per il primo profilo
            if profile_name == "Rediscover":
                print("\n--- DEBUG: Tutti gli span ---")
                spans = self.driver.find_elements(By.TAG_NAME, "span")
                for s in spans:
                    try:
                        txt = s.text.strip()
                        if txt:
                            print(f"[span] {txt}")
                    except Exception:
                        pass
                print("\n--- DEBUG: Tutti i div ---")
                divs = self.driver.find_elements(By.TAG_NAME, "div")
                for d in divs:
                    try:
                        txt = d.text.strip()
                        if txt:
                            print(f"[div] {txt}")
                    except Exception:
                        pass
            
            # Nuovo algoritmo: estrai i dati direttamente dagli span
            spans = self.driver.find_elements(By.TAG_NAME, "span")
            articles_found = False
            sales_found = False
            
            for s in spans:
                txt = s.text.strip()
                if txt.endswith("items for sale") or txt.endswith("item for sale"):
                    try:
                        articles = int(txt.split()[0].replace(',', '').replace('.', ''))
                        articles_found = True
                        logger.debug(f"  📦 {profile_name}: Trovati {articles} articoli")
                    except Exception as e:
                        logger.warning(f"  ⚠️  {profile_name}: Errore parsing articoli da '{txt}': {e}")
                        pass
                if txt.endswith("sold") and not txt.endswith("items sold"):  # Evita confusione con altre frasi
                    try:
                        sales = int(txt.split()[0].replace(',', '').replace('.', ''))
                        sales_found = True
                        logger.debug(f"  💰 {profile_name}: Trovate {sales} vendite")
                    except Exception as e:
                        logger.warning(f"  ⚠️  {profile_name}: Errore parsing vendite da '{txt}': {e}")
                        pass
            
            # Verifica se i dati sono stati trovati
            if not articles_found and not sales_found:
                logger.error(f"❌ {profile_name}: Nessun dato trovato nella pagina!")
                # Salva screenshot per debug se necessario
                if hasattr(self.driver, 'save_screenshot'):
                    try:
                        screenshot_path = f"debug_{profile_name}_{int(time.time())}.png"
                        self.driver.save_screenshot(screenshot_path)
                        logger.info(f"  📸 Screenshot salvato: {screenshot_path}")
                    except:
                        pass
                
                raise Exception("Nessun dato trovato nella pagina")
            elif not articles_found:
                logger.warning(f"⚠️  {profile_name}: Articoli non trovati, uso 0")
            elif not sales_found:
                logger.warning(f"⚠️  {profile_name}: Vendite non trovate, uso 0")
            
            parse_time = time.time() - parse_start
            total_profile_time = time.time() - profile_start_time
            
            # Salva statistiche profilo
            self.performance_stats["profile_times"][profile_name] = {
                "total_time": total_profile_time,
                "page_load_time": page_load_time,
                "parse_time": parse_time,
                "articles": articles,
                "sales": sales,
                "data_found": articles_found or sales_found
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
            
            logger.info(f"✅ {profile_name}: {articles} articoli, {sales} vendite (⏱️ {total_profile_time:.2f}s)")
            return {
                "name": profile_name,
                "profile_id": profile_id,
                "url": url,
                "articles": articles,
                "sales": sales,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "success": True,
                "data_quality": {
                    "articles_found": articles_found,
                    "sales_found": sales_found,
                    "page_title": page_title
                },
                "performance": {
                    "total_time": total_profile_time,
                    "page_load_time": page_load_time,
                    "parse_time": parse_time
                }
            }
        except Exception as e:
            total_profile_time = time.time() - profile_start_time
            logger.error(f"❌ Errore nello scraping del profilo {profile_name}: {e}")
            return {
                "name": profile_name,
                "profile_id": profile_id,
                "url": url,
                "articles": 0,
                "sales": 0,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "success": False,
                "error": str(e),
                "performance": {
                    "total_time": total_profile_time,
                    "page_load_time": 0,
                    "parse_time": 0
                }
            }
    
    def scrape_all_profiles(self) -> List[Dict]:
        """Scrapa tutti i profili configurati"""
        if not self.driver:
            self.setup_driver()
        
        results = []
        scraping_start_time = time.time()
        
        try:
            total_profiles = len(self.profiles)
            logger.info(f"🚀 Avvio scraping di {total_profiles} profili...")
            
            for i, (profile_name, profile_id) in enumerate(self.profiles.items(), 1):
                logger.info(f"📊 Progresso: {i}/{total_profiles}")
                
                result = self.scrape_profile(profile_name, profile_id)
                results.append(result)
                
                # Pausa tra le richieste per evitare rate limiting
                if i < total_profiles:  # Non aspettare dopo l'ultimo profilo
                    logger.info("⏳ Pausa 3 secondi...")
                    time.sleep(3)
                
        except Exception as e:
            logger.error(f"Errore generale nello scraping: {e}")
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
        print("📊 REPORT PERFORMANCE SCRAPING")
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
            print(f"{name:20} | {data['total_time']:6.2f}s | Load: {data['page_load_time']:5.2f}s | Parse: {data['parse_time']:5.2f}s")
        
        # Calcolo efficienza
        total_wait_time = (len(self.profiles) - 1) * 3  # 3 secondi tra profili
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