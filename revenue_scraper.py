"""
Revenue Scraper - Scraper parallelo per analisi ricavi
Modulo per estrarre prezzi degli articoli venduti dai profili Vestiaire Collective
"""

import time
import logging
import re
import concurrent.futures
import threading
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
    
    def _handle_cookie_banner(self):
        """Gestisce il banner dei cookie"""
        try:
            # Selettori per il banner cookie
            cookie_selectors = [
                "//button[contains(text(), 'Accetta')]",
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'OK')]",
                "//button[contains(text(), 'Consenti')]",
                "//button[contains(text(), 'Allow')]",
                "//div[contains(@class, 'cookie')]//button",
                "//div[contains(@class, 'banner')]//button",
                "//button[contains(@class, 'accept')]",
                "//button[contains(@class, 'cookie')]"
            ]
            
            for selector in cookie_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            element.click()
                            logger.debug("  🍪 Banner cookie gestito")
                            time.sleep(1)
                            return
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"  ⚠️ Errore gestione cookie: {e}")
    
    def _activate_sold_toggle(self, profile_name: str) -> bool:
        """Attiva il toggle per gli articoli venduti"""
        try:
            # Prima verifica se il toggle è già attivo
            toggle_active = False
            active_selectors = [
                "//div[contains(@class, 'toggle') and contains(@class, 'active')]",
                "//button[contains(@class, 'toggle') and contains(@class, 'active')]",
                "//div[contains(@class, 'switch') and contains(@class, 'active')]",
                "//input[@type='checkbox' and @checked]",
                "//div[contains(@class, 'filter') and contains(@class, 'active')]"
            ]
            
            for selector in active_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        toggle_active = True
                        logger.debug(f"  ✅ Toggle articoli venduti già attivo per {profile_name}")
                        return True
                except Exception:
                    continue
            
            # Se non è attivo, cerca di attivarlo
            logger.debug(f"  🔄 Attivando toggle articoli venduti per {profile_name}")
            
            toggle_selectors = [
                "//div[contains(text(), 'Articoli venduti')]",
                "//button[contains(text(), 'Articoli venduti')]",
                "//span[contains(text(), 'Articoli venduti')]",
                "//div[contains(text(), 'venduti')]",
                "//button[contains(text(), 'venduti')]",
                "//span[contains(text(), 'venduti')]",
                "//div[contains(@class, 'toggle')]",
                "//button[contains(@class, 'toggle')]",
                "//div[contains(@class, 'switch')]",
                "//input[@type='checkbox']"
            ]
            
            for selector in toggle_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                # Scroll per assicurarsi che sia visibile
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                                time.sleep(1)
                                
                                # Clicca sul toggle
                                element.click()
                                time.sleep(2)  # Attendi caricamento
                                
                                logger.debug(f"  ✅ Toggle cliccato con selettore: {selector}")
                                return True
                        except Exception as e:
                            logger.debug(f"  ⚠️ Errore clic toggle: {e}")
                            continue
                except Exception:
                    continue
            
            logger.warning(f"  ⚠️ Toggle articoli venduti non trovato per {profile_name}")
            return False
            
        except Exception as e:
            logger.error(f"  ❌ Errore attivazione toggle: {e}")
            return False
    
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
            
            # Gestione cookie banner
            self._handle_cookie_banner()
            
            # Verifica se la pagina è caricata correttamente
            page_title = self.driver.title
            if "403" in page_title or "404" in page_title or "error" in page_title.lower():
                logger.error(f"❌ Pagina di errore rilevata per {profile_name}: {page_title}")
                raise Exception(f"Pagina di errore: {page_title}")
            
            # Misurazione tempo di parsing
            parse_start = time.time()
            
            # Attiva il toggle per gli articoli venduti
            toggle_activated = self._activate_sold_toggle(profile_name)
            
            # Fallback: cerca anche il tab "sold" o "venduti"
            sold_tab_found = False
            if not toggle_activated:
                logger.debug(f"  📍 Cercando tab sold/venduti come fallback per {profile_name}")
                
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
        """Scrapa i ricavi per tutti i profili configurati"""
        logger.info("🚀 Avvio scraping ricavi per tutti i profili...")
        
        start_time = time.time()
        results = []
        
        try:
            # Usa processing parallelo per ottimizzare le performance
            results = self._scrape_profiles_parallel()
            
        except Exception as e:
            logger.error(f"❌ Errore critico nello scraping parallelo: {e}")
            # Fallback allo scraping sequenziale
            logger.info("🔄 Fallback allo scraping sequenziale...")
            results = self._scrape_profiles_sequential()
        
        # Calcola statistiche performance
        total_time = time.time() - start_time
        self.performance_stats["total_scraping_time"] = total_time
        
        if results:
            profile_times = [r.get("performance", {}).get("total_time", 0) for r in results if r.get("success")]
            if profile_times:
                self.performance_stats["average_profile_time"] = sum(profile_times) / len(profile_times)
                
                # Trova profilo più veloce e più lento
                fastest_idx = profile_times.index(min(profile_times))
                slowest_idx = profile_times.index(max(profile_times))
                
                self.performance_stats["fastest_profile"] = {
                    "name": results[fastest_idx]["name"],
                    "time": profile_times[fastest_idx]
                }
                self.performance_stats["slowest_profile"] = {
                    "name": results[slowest_idx]["name"],
                    "time": profile_times[slowest_idx]
                }
        
        self._log_performance_summary()
        return results
    
    def _scrape_profiles_parallel(self, max_workers: int = None) -> List[Dict]:
        """Scrapa i profili in parallelo usando ThreadPoolExecutor"""
        if max_workers is None:
            # Carica configurazione
            try:
                from config import OPTIMIZATION_CONFIG
                max_workers = OPTIMIZATION_CONFIG.get("max_parallel_workers", 3)
            except ImportError:
                max_workers = 3
        
        logger.info(f"⚡ Avvio scraping parallelo con {max_workers} workers...")
        
        results = []
        
        # Crea un lock per thread safety
        lock = threading.Lock()
        
        def scrape_single_profile(profile_data):
            """Funzione per scraping singolo profilo"""
            profile_name, profile_id = profile_data
            
            # Crea un nuovo driver per ogni thread
            thread_driver = None
            try:
                thread_driver = self._create_thread_driver()
                
                # Crea una nuova istanza dello scraper per questo thread
                thread_scraper = RevenueScraper(profiles={profile_name: profile_id}, 
                                              existing_sales_data=self.existing_sales_data)
                thread_scraper.driver = thread_driver
                
                result = thread_scraper.scrape_profile_revenue(profile_name, profile_id)
                
                # Thread-safe logging
                with lock:
                    logger.info(f"✅ Completato {profile_name} (thread)")
                
                return result
                
            except Exception as e:
                logger.error(f"❌ Errore thread {profile_name}: {e}")
                return {
                    "name": profile_name,
                    "profile_id": profile_id,
                    "success": False,
                    "error": str(e),
                    "sold_items_count": 0,
                    "total_revenue": 0.0,
                    "sold_items_prices": [],
                    "performance": {"page_load_time": 0, "parse_time": 0, "total_time": 0},
                    "data_quality": {"items_found": False, "real_sold_count_found": False, "page_title": "", "price_elements_found": 0}
                }
            finally:
                if thread_driver:
                    try:
                        thread_driver.quit()
                    except:
                        pass
        
        # Esegui scraping parallelo
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Sottometti tutti i lavori
            future_to_profile = {
                executor.submit(scrape_single_profile, (name, id)): (name, id) 
                for name, id in self.profiles.items()
            }
            
            # Raccogli i risultati
            for future in concurrent.futures.as_completed(future_to_profile):
                profile_name, profile_id = future_to_profile[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"❌ Errore futuro per {profile_name}: {e}")
                    results.append({
                        "name": profile_name,
                        "profile_id": profile_id,
                        "success": False,
                        "error": str(e),
                        "sold_items_count": 0,
                        "total_revenue": 0.0,
                        "sold_items_prices": [],
                        "performance": {"page_load_time": 0, "parse_time": 0, "total_time": 0},
                        "data_quality": {"items_found": False, "real_sold_count_found": False, "page_title": "", "price_elements_found": 0}
                    })
        
        return results
    
    def _scrape_profiles_sequential(self) -> List[Dict]:
        """Scrapa i profili in modo sequenziale (fallback)"""
        logger.info("🔄 Avvio scraping sequenziale...")
        
        if not self.driver:
            self.setup_driver()
        
        results = []
        
        try:
            for profile_name, profile_id in self.profiles.items():
                try:
                    result = self.scrape_profile_revenue(profile_name, profile_id)
                    results.append(result)
                    
                    # Pausa tra i profili per evitare rate limiting
                    if len(results) < len(self.profiles):
                        time.sleep(3)
                        
                except Exception as e:
                    logger.error(f"❌ Errore scraping profilo {profile_name}: {e}")
                    results.append({
                        "name": profile_name,
                        "profile_id": profile_id,
                        "success": False,
                        "error": str(e),
                        "sold_items_count": 0,
                        "total_revenue": 0.0,
                        "sold_items_prices": [],
                        "performance": {"page_load_time": 0, "parse_time": 0, "total_time": 0},
                        "data_quality": {"items_found": False, "real_sold_count_found": False, "page_title": "", "price_elements_found": 0}
                    })
        
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
        
        return results
    
    def _create_thread_driver(self):
        """Crea un nuovo driver Chrome per un thread"""
        try:
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
            
            service = Service(driver_path)
            return webdriver.Chrome(service=service, options=chrome_options)
            
        except Exception as e:
            logger.error(f"Errore creazione thread driver: {e}")
            raise
    
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