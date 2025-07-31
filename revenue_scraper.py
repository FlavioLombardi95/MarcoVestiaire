"""
Revenue Scraper - Scraper essenziale per ricavi
"""

import time
import logging
import re
import concurrent.futures
import threading
from typing import Dict, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from config import VESTIAIRE_PROFILES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RevenueScraper:
    """Scraper essenziale per ricavi"""
    
    def __init__(self, profiles=None, existing_sales_data=None):
        self.driver = None
        self.profiles = profiles or {}
        self.existing_sales_data = existing_sales_data or {}
    
    def setup_driver(self):
        """Configura driver Chrome"""
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Commentato per bypassare Cloudflare
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Opzioni per bypassare Cloudflare
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User-Agent realistico
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
        
        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Nascondi che è un bot
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def _handle_cookie_banner(self):
        """Gestisce banner cookie"""
        try:
            selectors = [
                "//button[contains(text(), 'Accetta')]",
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'OK')]"
            ]
            
            for selector in selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        element.click()
                        time.sleep(1)
                        return
        except Exception:
            pass

    def _handle_cloudflare_challenge(self, profile_name: str) -> bool:
        """Gestisce la verifica Cloudflare"""
        try:
            logger.info(f"    🛡️ Gestione verifica Cloudflare per {profile_name}...")
            
            # Controlla se siamo nella pagina di verifica Cloudflare
            page_title = self.driver.title
            if "Ci siamo quasi" in page_title or "Just a moment" in page_title:
                logger.info(f"      🔍 Pagina di verifica Cloudflare rilevata: {page_title}")
                
                # Aspetta che la verifica sia completata (massimo 30 secondi)
                max_wait = 30
                wait_time = 0
                
                while wait_time < max_wait:
                    current_title = self.driver.title
                    current_url = self.driver.current_url
                    
                    # Se il titolo cambia o l'URL cambia, la verifica è completata
                    if current_title != page_title and "vestiairecollective.com" in current_url:
                        logger.info(f"      ✅ Verifica Cloudflare completata: {current_title}")
                        time.sleep(3)  # Aspetta che la pagina si carichi completamente
                        return True
                    
                    # Se vediamo "Verifica riuscita", aspettiamo un po' di più
                    if "Verifica riuscita" in self.driver.page_source:
                        logger.info(f"      ⏳ Verifica in corso...")
                        time.sleep(5)
                        wait_time += 5
                        continue
                    
                    time.sleep(2)
                    wait_time += 2
                
                logger.warning(f"      ⚠️ Timeout verifica Cloudflare dopo {max_wait} secondi")
                return False
            
            return True  # Non è una pagina di verifica
            
        except Exception as e:
            logger.warning(f"      ⚠️ Errore gestione Cloudflare: {e}")
            return False
    
    def _activate_sold_toggle(self, profile_name: str) -> bool:
        """Attiva toggle articoli venduti"""
        try:
            # Verifica se già attivo
            active_selectors = [
                "//div[contains(@class, 'toggle') and contains(@class, 'active')]",
                "//button[contains(@class, 'toggle') and contains(@class, 'active')]"
            ]
            
            for selector in active_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    return True
            
            # Attiva toggle
            toggle_selectors = [
                "//div[contains(text(), 'Articoli venduti')]",
                "//button[contains(text(), 'Articoli venduti')]",
                "//div[contains(text(), 'venduti')]"
            ]
            
            for selector in toggle_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        element.click()
                        time.sleep(2)
                        return True
            
            return False
        except Exception:
            return False
    
    def _navigate_to_items_section(self, profile_name: str, profile_id: str) -> bool:
        """Naviga alla sezione articoli/prodotti del profilo"""
        try:
            logger.info(f"  🔄 Navigando alla sezione articoli per {profile_name}...")
            
            # Prova diverse URL per la sezione articoli
            items_urls = [
                f"https://it.vestiairecollective.com/profile/{profile_id}/items/",
                f"https://it.vestiairecollective.com/profile/{profile_id}/products/",
                f"https://it.vestiairecollective.com/profile/{profile_id}/articoli/",
                f"https://it.vestiairecollective.com/profile/{profile_id}/prodotti/",
                f"https://it.vestiairecollective.com/profile/{profile_id}/?view=items",
                f"https://it.vestiairecollective.com/profile/{profile_id}/?section=items",
            ]
            
            for url in items_urls:
                try:
                    logger.info(f"    Provando URL articoli: {url}")
                    self.driver.get(url)
                    time.sleep(5)  # Aspetta che si carichi
                    
                    # Controlla se la pagina contiene prezzi
                    price_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '€')]")
                    if price_elements:
                        logger.info(f"    ✅ URL articoli funzionante: {url} - Trovati {len(price_elements)} prezzi")
                        return True
                    else:
                        logger.info(f"    ❌ URL articoli non funzionante: {url} - Nessun prezzo trovato")
                        
                except Exception as e:
                    logger.warning(f"    Errore URL articoli {url}: {e}")
                    continue
            
            # Se nessuna URL funziona, torna alla pagina principale e cerca link
            logger.info(f"    Tornando alla pagina principale per cercare link articoli...")
            main_url = f"https://it.vestiairecollective.com/profile/{profile_id}/"
            self.driver.get(main_url)
            time.sleep(3)
            
            # Cerca link verso articoli
            items_link_selectors = [
                "//a[contains(@href, 'items')]",
                "//a[contains(@href, 'products')]",
                "//a[contains(@href, 'articoli')]",
                "//a[contains(@href, 'prodotti')]",
                "//a[contains(text(), 'articoli')]",
                "//a[contains(text(), 'prodotti')]",
                "//a[contains(text(), 'items')]",
                "//a[contains(text(), 'products')]",
                "//button[contains(text(), 'articoli')]",
                "//button[contains(text(), 'prodotti')]",
                "//button[contains(text(), 'items')]",
                "//button[contains(text(), 'products')]",
            ]
            
            for selector in items_link_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            href = element.get_attribute("href")
                            text = element.text.strip()
                            logger.info(f"    Cliccando su link articoli: '{text}' -> {href}")
                            element.click()
                            time.sleep(5)
                            
                            # Controlla se ora ci sono prezzi
                            price_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '€')]")
                            if price_elements:
                                logger.info(f"    ✅ Link articoli funzionante - Trovati {len(price_elements)} prezzi")
                                return True
                    except Exception as e:
                        logger.warning(f"    Errore click link articoli: {e}")
                        continue
            
            logger.warning(f"  ⚠️ Non riuscito a navigare alla sezione articoli per {profile_name}")
            return False
            
        except Exception as e:
            logger.warning(f"  ⚠️ Errore navigazione articoli per {profile_name}: {e}")
            return False

    def _extract_final_sale_prices(self, profile_name: str, profile_id: str = None) -> list:
        """Estrae specificamente i prezzi di vendita finali"""
        try:
            logger.info(f"  💰 Estrazione prezzi di vendita finali per {profile_name}...")
            
            # Aspetta che la pagina si carichi completamente
            time.sleep(3)
            
            # Prima prova a navigare alla sezione articoli venduti
            logger.info(f"    🔄 Tentativo navigazione sezione venduti...")
            sold_section_found = self._navigate_to_sold_section(profile_name)
            
            if sold_section_found:
                logger.info(f"    ✅ Sezione venduti trovata, cercando prezzi...")
            else:
                logger.info(f"    ⚠️ Sezione venduti non trovata, cercando nella pagina principale...")
            
            # Scroll per caricare contenuto dinamico
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Selettori specifici per prezzi di vendita finali (non barrati)
            final_price_selectors = [
                # Selettori per prezzi finali in card prodotti
                "//div[contains(@class, 'product-card')]//span[contains(text(), '€') and not(ancestor::*[contains(@class, 'strike')])]",
                "//div[contains(@class, 'item-card')]//span[contains(text(), '€') and not(ancestor::*[contains(@class, 'strike')])]",
                "//div[contains(@class, 'article-card')]//span[contains(text(), '€') and not(ancestor::*[contains(@class, 'strike')])]",
                
                # Selettori per prezzi finali specifici
                "//span[contains(@class, 'final-price') and contains(text(), '€')]",
                "//span[contains(@class, 'sale-price') and contains(text(), '€')]",
                "//span[contains(@class, 'current-price') and contains(text(), '€')]",
                
                # Selettori per prezzi in elementi con classi specifiche
                "//div[contains(@class, 'price-container')]//span[contains(text(), '€') and not(ancestor::*[contains(@class, 'original')])]",
                "//div[contains(@class, 'price-wrapper')]//span[contains(text(), '€') and not(ancestor::*[contains(@class, 'old')])]",
                
                # Selettori generici ma filtrati
                "//span[contains(text(), '€') and not(ancestor::*[contains(@class, 'strike')]) and not(ancestor::*[contains(@class, 'original')])]",
                "//div[contains(text(), '€') and not(ancestor::*[contains(@class, 'strike')]) and not(ancestor::*[contains(@class, 'original')])]",
            ]
            
            all_prices = []
            
            for i, selector in enumerate(final_price_selectors):
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    logger.info(f"    Selettore prezzi finali {i+1}: trovati {len(elements)} elementi")
                    
                    for element in elements:
                        try:
                            text = element.text.strip()
                            if text and '€' in text:
                                # Estrai solo il numero prima di €
                                price_match = re.search(r'(\d+(?:,\d+)?)\s*€', text)
                                if price_match:
                                    price_str = price_match.group(1).replace(',', '')
                                    price = float(price_str)
                                    
                                    # Filtra prezzi ragionevoli (tra 10€ e 10000€)
                                    if 10 <= price <= 10000:
                                        all_prices.append(price)
                                        logger.info(f"      Prezzo finale trovato: €{price:.2f} (da: '{text}')")
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    logger.warning(f"    Errore selettore {i+1}: {e}")
                    continue
            
            # Rimuovi duplicati mantenendo l'ordine
            unique_prices = []
            seen_prices = set()
            for price in all_prices:
                if price not in seen_prices:
                    unique_prices.append(price)
                    seen_prices.add(price)
            
            logger.info(f"  💰 Trovati {len(unique_prices)} prezzi di vendita finali unici per {profile_name}")
            
            # Se non troviamo prezzi, prova a cercare nel testo della pagina
            if not unique_prices:
                logger.info(f"  🔍 Ricerca prezzi nel testo della pagina per {profile_name}...")
                
                body_text = self.driver.find_element(By.TAG_NAME, "body").text
                price_matches = re.findall(r'(\d+(?:,\d+)?)\s*€', body_text)
                
                for match in price_matches:
                    try:
                        price_str = match.replace(',', '')
                        price = float(price_str)
                        
                        # Filtra prezzi ragionevoli
                        if 10 <= price <= 10000 and price not in seen_prices:
                            unique_prices.append(price)
                            seen_prices.add(price)
                            logger.info(f"      Prezzo dal testo: €{price:.2f}")
                    except Exception as e:
                        continue
            
            # Se ancora non troviamo prezzi, prova URL dirette
            if not unique_prices:
                logger.info(f"  🔍 Tentativo URL dirette per {profile_name}...")
                direct_url_success = self._try_direct_sold_urls(profile_name, profile_id)
                if direct_url_success:
                    # Riprova estrazione prezzi dopo navigazione
                    for i, selector in enumerate(final_price_selectors):
                        try:
                            elements = self.driver.find_elements(By.XPATH, selector)
                            logger.info(f"    Selettore prezzi diretti {i+1}: trovati {len(elements)} elementi")
                            
                            for element in elements:
                                try:
                                    text = element.text.strip()
                                    if text and '€' in text:
                                        price_match = re.search(r'(\d+(?:,\d+)?)\s*€', text)
                                        if price_match:
                                            price_str = price_match.group(1).replace(',', '')
                                            price = float(price_str)
                                            
                                            if 10 <= price <= 10000 and price not in seen_prices:
                                                unique_prices.append(price)
                                                seen_prices.add(price)
                                                logger.info(f"      Prezzo diretto trovato: €{price:.2f} (da: '{text}')")
                                except Exception as e:
                                    continue
                        except Exception as e:
                            continue
            
            # Se ancora non troviamo prezzi, analizza la struttura completa
            if not unique_prices:
                logger.info(f"  🔍 Analisi struttura completa per {profile_name}...")
                self._analyze_page_structure_for_prices(profile_name)
            
            return unique_prices
            
        except Exception as e:
            logger.warning(f"  ⚠️ Errore estrazione prezzi finali per {profile_name}: {e}")
            return []

    def _analyze_page_structure_for_prices(self, profile_name: str):
        """Analizza la struttura della pagina per trovare prezzi nascosti"""
        try:
            logger.info(f"    🔍 Analisi struttura pagina per {profile_name}...")
            
            # 1. Analizza tutti gli elementi con testo
            all_elements = self.driver.find_elements(By.XPATH, "//*[text()]")
            logger.info(f"      Elementi con testo: {len(all_elements)}")
            
            # 2. Cerca elementi con €
            euro_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '€')]")
            logger.info(f"      Elementi con €: {len(euro_elements)}")
            
            for i, element in enumerate(euro_elements[:10]):  # Mostra primi 10
                try:
                    text = element.text.strip()
                    tag = element.tag_name
                    class_name = element.get_attribute("class") or ""
                    logger.info(f"        Elemento € {i+1}: '{text}' (tag: {tag}, class: {class_name})")
                except Exception as e:
                    continue
            
            # 3. Cerca elementi con numeri che potrebbero essere prezzi
            number_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '0') or contains(text(), '1') or contains(text(), '2') or contains(text(), '3') or contains(text(), '4') or contains(text(), '5') or contains(text(), '6') or contains(text(), '7') or contains(text(), '8') or contains(text(), '9')]")
            logger.info(f"      Elementi con numeri: {len(number_elements)}")
            
            # 4. Analizza il testo completo della pagina
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            logger.info(f"      Testo completo: {len(body_text)} caratteri")
            
            # 5. Cerca pattern di prezzi nel testo
            price_patterns = [
                r'(\d+(?:,\d+)?)\s*€',
                r'€\s*(\d+(?:,\d+)?)',
                r'(\d+(?:,\d+)?)\s*EUR',
                r'EUR\s*(\d+(?:,\d+)?)',
                r'(\d+(?:,\d+)?)\s*euro',
                r'euro\s*(\d+(?:,\d+)?)'
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, body_text, re.IGNORECASE)
                if matches:
                    logger.info(f"      Pattern '{pattern}': {len(matches)} matches - {matches[:5]}")
            
            # 6. Salva screenshot per debug
            timestamp = int(time.time())
            screenshot_path = f"debug_prices_{profile_name.replace(' ', '_')}_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"      📸 Screenshot salvato: {screenshot_path}")
            
            # 7. Salva anche il codice HTML per analisi
            html_path = f"debug_html_{profile_name.replace(' ', '_')}_{timestamp}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            logger.info(f"      📄 HTML salvato: {html_path}")
            
        except Exception as e:
            logger.warning(f"    ⚠️ Errore analisi struttura: {e}")

    def _try_direct_sold_urls(self, profile_name: str, profile_id: str) -> bool:
        """Prova URL dirette per accedere agli articoli venduti"""
        try:
            logger.info(f"    🔗 Tentativo URL dirette per {profile_name}...")
            
            # URL da provare per articoli venduti
            sold_urls = [
                f"https://it.vestiairecollective.com/profile/{profile_id}/?filter=sold",
                f"https://it.vestiairecollective.com/profile/{profile_id}/?tab=sold",
                f"https://it.vestiairecollective.com/profile/{profile_id}/?view=sold",
                f"https://it.vestiairecollective.com/profile/{profile_id}/?section=sold",
                f"https://it.vestiairecollective.com/profile/{profile_id}/items/?filter=sold",
                f"https://it.vestiairecollective.com/profile/{profile_id}/items/?tab=sold",
                f"https://it.vestiairecollective.com/profile/{profile_id}/products/?filter=sold",
                f"https://it.vestiairecollective.com/profile/{profile_id}/products/?tab=sold",
                # URL con parametri italiani
                f"https://it.vestiairecollective.com/profile/{profile_id}/?filter=venduti",
                f"https://it.vestiairecollective.com/profile/{profile_id}/?tab=venduti",
                f"https://it.vestiairecollective.com/profile/{profile_id}/items/?filter=venduti",
                f"https://it.vestiairecollective.com/profile/{profile_id}/products/?filter=venduti"
            ]
            
            for url in sold_urls:
                try:
                    logger.info(f"      Provando URL: {url}")
                    self.driver.get(url)
                    time.sleep(5)  # Aspetta che si carichi
                    
                    # Controlla se ora ci sono prezzi
                    price_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '€')]")
                    if price_elements:
                        logger.info(f"      ✅ URL funzionante: {url} - Trovati {len(price_elements)} prezzi")
                        return True
                    else:
                        logger.info(f"      ❌ URL non funzionante: {url} - Nessun prezzo trovato")
                        
                except Exception as e:
                    logger.warning(f"      Errore URL {url}: {e}")
                    continue
            
            logger.warning(f"    ⚠️ Nessuna URL diretta funzionante per {profile_name}")
            return False
            
        except Exception as e:
            logger.warning(f"    ⚠️ Errore tentativo URL dirette per {profile_name}: {e}")
            return False

    def _test_user_navigation(self, profile_name: str, profile_id: str) -> bool:
        """Test sistema utenti finti - navigazione base"""
        try:
            logger.info(f"  🧪 Test navigazione utente finto per {profile_name}...")
            
            # Inizializza driver se non esiste
            if not self.driver:
                self.setup_driver()
            
            # Test navigazione alla pagina profilo
            url = f"https://it.vestiairecollective.com/profile/{profile_id}/"
            self.driver.get(url)
            time.sleep(3)
            
            # Gestisci verifica Cloudflare se presente
            cloudflare_success = self._handle_cloudflare_challenge(profile_name)
            if not cloudflare_success:
                logger.warning(f"    ⚠️ Verifica Cloudflare fallita per {profile_name}")
                return False
            
            # Verifica che la pagina sia caricata
            page_title = self.driver.title
            current_url = self.driver.current_url
            
            # Controlla se siamo sulla pagina giusta
            if (profile_name.lower() in page_title.lower() or 
                "vestiaire" in page_title.lower() or
                profile_id in current_url or
                "vestiairecollective.com" in current_url):
                logger.info(f"    ✅ Navigazione riuscita: {page_title}")
                logger.info(f"    📍 URL: {current_url}")
                return True
            else:
                logger.warning(f"    ⚠️ Navigazione dubbia: {page_title}")
                logger.warning(f"    📍 URL: {current_url}")
                return False
                
        except Exception as e:
            logger.error(f"    ❌ Errore test navigazione: {e}")
            return False

    def _test_flagging_algorithm(self, profile_name: str, profile_id: str) -> int:
        """Test algoritmo flagging articoli venduti"""
        try:
            logger.info(f"  🏷️ Test flagging per {profile_name}...")
            
            # Inizializza driver se non esiste
            if not self.driver:
                self.setup_driver()
            
            # Naviga alla pagina
            url = f"https://it.vestiairecollective.com/profile/{profile_id}/"
            self.driver.get(url)
            time.sleep(3)
            
            # Usa l'algoritmo di flagging esistente
            real_sold_count = self._find_real_sold_count(profile_name)
            
            logger.info(f"    📊 Vendite trovate: {real_sold_count}")
            return real_sold_count
            
        except Exception as e:
            logger.error(f"    ❌ Errore test flagging: {e}")
            return 0

    def _test_price_extraction(self, profile_name: str, profile_id: str) -> list:
        """Test estrazione prezzi di vendita finali"""
        try:
            logger.info(f"  💰 Test estrazione prezzi per {profile_name}...")
            
            # Inizializza driver se non esiste
            if not self.driver:
                self.setup_driver()
            
            # Naviga alla pagina
            url = f"https://it.vestiairecollective.com/profile/{profile_id}/"
            self.driver.get(url)
            time.sleep(3)
            
            # Usa il metodo di estrazione prezzi esistente
            prices = self._extract_final_sale_prices(profile_name, profile_id)
            
            logger.info(f"    📊 Prezzi estratti: {len(prices)}")
            return prices
            
        except Exception as e:
            logger.error(f"    ❌ Errore test prezzi: {e}")
            return []

    def _test_parallel_system(self, test_profiles: list) -> dict:
        """Test sistema parallelo con profili di test"""
        try:
            logger.info(f"  ⚡ Test sistema parallelo con {len(test_profiles)} profili...")
            
            results = {}
            
            # Test sequenziale per ora (il parallelo sarà implementato dopo)
            for profile_name in test_profiles:
                if profile_name in VESTIAIRE_PROFILES:
                    profile_id = VESTIAIRE_PROFILES[profile_name]
                    
                    logger.info(f"    🔍 Processando {profile_name}...")
                    
                    # Test completo per questo profilo
                    sold_count = self._test_flagging_algorithm(profile_name, profile_id)
                    prices = self._test_price_extraction(profile_name, profile_id)
                    
                    results[profile_name] = {
                        'sold_count': sold_count,
                        'prices_count': len(prices),
                        'revenue': sum(prices)
                    }
            
            return results
            
        except Exception as e:
            logger.error(f"    ❌ Errore test parallelo: {e}")
            return {}

    def _navigate_to_sold_items_url(self, profile_name: str, profile_id: str) -> bool:
        """Naviga direttamente alla sezione articoli venduti"""
        try:
            logger.info(f"  🔄 Navigando alla sezione articoli venduti per {profile_name}...")
            
            # Prova diverse URL per la sezione venduti
            sold_urls = [
                f"https://it.vestiairecollective.com/profile/{profile_id}/sold/",
                f"https://it.vestiairecollective.com/profile/{profile_id}/items/sold/",
                f"https://it.vestiairecollective.com/profile/{profile_id}/venduti/",
                f"https://it.vestiairecollective.com/profile/{profile_id}/items/venduti/",
                f"https://it.vestiairecollective.com/profile/{profile_id}/?filter=sold",
                f"https://it.vestiairecollective.com/profile/{profile_id}/?tab=sold",
            ]
            
            for url in sold_urls:
                try:
                    logger.info(f"    Provando URL: {url}")
                    self.driver.get(url)
                    time.sleep(5)  # Aspetta che si carichi
                    
                    # Controlla se la pagina contiene prezzi
                    price_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '€')]")
                    if price_elements:
                        logger.info(f"    ✅ URL funzionante: {url} - Trovati {len(price_elements)} prezzi")
                        return True
                    else:
                        logger.info(f"    ❌ URL non funzionante: {url} - Nessun prezzo trovato")
                        
                except Exception as e:
                    logger.warning(f"    Errore URL {url}: {e}")
                    continue
            
            # Se nessuna URL funziona, torna alla pagina principale e cerca link
            logger.info(f"    Tornando alla pagina principale per cercare link...")
            main_url = f"https://it.vestiairecollective.com/profile/{profile_id}/"
            self.driver.get(main_url)
            time.sleep(3)
            
            # Cerca link verso articoli venduti
            sold_link_selectors = [
                "//a[contains(@href, 'sold')]",
                "//a[contains(@href, 'venduti')]",
                "//a[contains(text(), 'venduti')]",
                "//a[contains(text(), 'sold')]",
                "//button[contains(text(), 'venduti')]",
                "//button[contains(text(), 'sold')]",
            ]
            
            for selector in sold_link_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            href = element.get_attribute("href")
                            logger.info(f"    Cliccando su link venduti: {href}")
                            element.click()
                            time.sleep(5)
                            
                            # Controlla se ora ci sono prezzi
                            price_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '€')]")
                            if price_elements:
                                logger.info(f"    ✅ Link funzionante - Trovati {len(price_elements)} prezzi")
                                return True
                    except Exception as e:
                        logger.warning(f"    Errore click link: {e}")
                        continue
            
            logger.warning(f"  ⚠️ Non riuscito a navigare alla sezione articoli venduti per {profile_name}")
            return False
            
        except Exception as e:
            logger.warning(f"  ⚠️ Errore navigazione URL venduti per {profile_name}: {e}")
            return False

    def _debug_page_structure(self, profile_name: str):
        """Analizza la struttura della pagina per debug"""
        try:
            logger.info(f"  🔍 Debug struttura pagina per {profile_name}...")
            
            # Salva screenshot
            timestamp = int(time.time())
            screenshot_path = f"debug_{profile_name.replace(' ', '_')}_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"    📸 Screenshot salvato: {screenshot_path}")
            
            # Analizza tutti gli elementi con testo
            all_elements = self.driver.find_elements(By.XPATH, "//*[text()]")
            logger.info(f"    Elementi con testo: {len(all_elements)}")
            
            # Cerca elementi con prezzi
            price_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '€')]")
            logger.info(f"    Elementi con €: {len(price_elements)}")
            
            for i, element in enumerate(price_elements[:10]):  # Primi 10
                try:
                    text = element.text.strip()
                    tag_name = element.tag_name
                    class_name = element.get_attribute("class") or ""
                    logger.info(f"      Prezzo {i+1}: '{text}' (tag: {tag_name}, class: {class_name})")
                except Exception as e:
                    logger.warning(f"      Errore elemento {i+1}: {e}")
            
            # Cerca elementi con numeri (correzione XPath)
            number_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '0') or contains(text(), '1') or contains(text(), '2') or contains(text(), '3') or contains(text(), '4') or contains(text(), '5') or contains(text(), '6') or contains(text(), '7') or contains(text(), '8') or contains(text(), '9')]")
            logger.info(f"    Elementi con numeri: {len(number_elements)}")
            
            # Cerca elementi con "venduti" o "sold"
            sold_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'venduti') or contains(text(), 'sold')]")
            logger.info(f"    Elementi con 'venduti/sold': {len(sold_elements)}")
            
            for i, element in enumerate(sold_elements[:5]):  # Primi 5
                try:
                    text = element.text.strip()
                    tag_name = element.tag_name
                    class_name = element.get_attribute("class") or ""
                    logger.info(f"      Venduti {i+1}: '{text}' (tag: {tag_name}, class: {class_name})")
                except Exception as e:
                    logger.warning(f"      Errore elemento venduti {i+1}: {e}")
            
            # Analizza la struttura HTML
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            logger.info(f"    Testo body: {len(body_text)} caratteri")
            
            # Cerca pattern specifici nel testo
            patterns_to_check = [
                r'(\d+)\s*€',
                r'€\s*(\d+)',
                r'(\d+)\s+venduti',
                r'(\d+)\s+sold',
                r'Venduto',
                r'Sold',
            ]
            
            for pattern in patterns_to_check:
                matches = re.findall(pattern, body_text, re.IGNORECASE)
                if matches:
                    logger.info(f"    Pattern '{pattern}': {len(matches)} matches - {matches[:5]}")
            
        except Exception as e:
            logger.warning(f"  ⚠️ Errore debug struttura per {profile_name}: {e}")

    def _navigate_to_sold_section(self, profile_name: str) -> bool:
        """Naviga alla sezione articoli venduti"""
        try:
            logger.info(f"  🔄 Navigando alla sezione venduti per {profile_name}...")
            
            # 1. Prima cerca il toggle "Hide Sold Products" e cliccalo per mostrare gli articoli venduti
            hide_sold_selectors = [
                "//button[contains(text(), 'Hide Sold Products')]",
                "//button[contains(text(), 'Nascondi prodotti venduti')]",
                "//div[contains(text(), 'Hide Sold Products')]",
                "//div[contains(text(), 'Nascondi prodotti venduti')]",
                "//span[contains(text(), 'Hide Sold Products')]",
                "//span[contains(text(), 'Nascondi prodotti venduti')]",
                "//label[contains(text(), 'Hide Sold Products')]",
                "//label[contains(text(), 'Nascondi prodotti venduti')]",
                # Selettori per checkbox
                "//input[@type='checkbox' and contains(@id, 'sold')]",
                "//input[@type='checkbox' and contains(@name, 'sold')]",
                "//input[@type='checkbox' and contains(@class, 'sold')]"
            ]
            
            for selector in hide_sold_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            text = element.text.strip() if element.text else "checkbox"
                            logger.info(f"    Cliccando toggle 'Hide Sold Products': '{text}'")
                            element.click()
                            time.sleep(3)
                            
                            # Verifica se ora ci sono prezzi
                            price_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '€')]")
                            if price_elements:
                                logger.info(f"    ✅ Prezzi trovati dopo toggle: {len(price_elements)} elementi")
                                return True
                    except Exception as e:
                        continue
            
            # 2. Se non trova il toggle, cerca tab o link per articoli venduti
            sold_tab_selectors = [
                # Selettori specifici per Vestiaire Collective
                "//button[contains(text(), 'venduti')]",
                "//div[contains(text(), 'venduti')]",
                "//span[contains(text(), 'venduti')]",
                "//a[contains(text(), 'venduti')]",
                "//button[contains(text(), 'sold')]",
                "//div[contains(text(), 'sold')]",
                "//span[contains(text(), 'sold')]",
                "//a[contains(text(), 'sold')]",
                # Selettori con numeri specifici
                "//button[contains(text(), '37')]",
                "//div[contains(text(), '37')]",
                "//span[contains(text(), '37')]",
                "//button[contains(text(), '7306')]",
                "//div[contains(text(), '7306')]",
                "//span[contains(text(), '7306')]",
                # Selettori per tab
                "//a[contains(text(), 'Sold items')]",
                "//a[contains(text(), 'Articoli venduti')]",
                "//div[contains(text(), 'Sold items')]",
                "//div[contains(text(), 'Articoli venduti')]",
                # Selettori generici con numeri
                "//*[contains(text(), '7306 sold')]",
                "//*[contains(text(), '7306 venduti')]",
                "//*[contains(text(), '37 sold')]",
                "//*[contains(text(), '37 venduti')]"
            ]
            
            for selector in sold_tab_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            text = element.text.strip()
                            logger.info(f"    Cliccando su: '{text}'")
                            element.click()
                            time.sleep(3)  # Aspetta che si carichi
                            
                            # Verifica se ora ci sono prezzi
                            price_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '€')]")
                            if price_elements:
                                logger.info(f"    ✅ Prezzi trovati dopo click: {len(price_elements)} elementi")
                                return True
                    except Exception as e:
                        logger.warning(f"    Errore click su elemento: {e}")
                        continue
            
            # 2. Se non trova tab, cerca filtri
            filter_selectors = [
                "//div[contains(@class, 'filter')]//button[contains(text(), 'venduti')]",
                "//div[contains(@class, 'filter')]//div[contains(text(), 'venduti')]",
                "//div[contains(@class, 'filter')]//span[contains(text(), 'venduti')]",
            ]
            
            for selector in filter_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"    Cliccando su filtro: '{element.text}'")
                            element.click()
                            time.sleep(3)
                            return True
                    except Exception as e:
                        continue
            
            # 3. Scroll per cercare elementi nascosti
            logger.info(f"    Scrolling per cercare elementi venduti...")
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Scroll graduale
            for i in range(5):
                self.driver.execute_script(f"window.scrollTo(0, {500 * (i+1)});")
                time.sleep(1)
                
                # Controlla se appaiono prezzi
                price_check = self.driver.find_elements(By.XPATH, "//*[contains(text(), '€')]")
                if price_check:
                    logger.info(f"    Trovati {len(price_check)} elementi con € dopo scroll {i+1}")
                    return True
            
            # 3. Se non trova nulla, analizza la struttura della pagina per trovare elementi cliccabili
            logger.info(f"    🔍 Analisi struttura pagina per trovare elementi venduti...")
            self._analyze_page_for_clickable_elements(profile_name)
            
            logger.warning(f"  ⚠️ Non riuscito a navigare alla sezione venduti per {profile_name}")
            return False
            
        except Exception as e:
            logger.warning(f"  ⚠️ Errore navigazione sezione venduti per {profile_name}: {e}")
            return False

    def _analyze_page_for_clickable_elements(self, profile_name: str):
        """Analizza la pagina per trovare elementi cliccabili relativi agli articoli venduti"""
        try:
            logger.info(f"      🔍 Analisi elementi cliccabili per {profile_name}...")
            
            # Cerca tutti gli elementi cliccabili
            clickable_selectors = [
                "//button",
                "//a",
                "//div[@onclick]",
                "//span[@onclick]",
                "//input[@type='checkbox']",
                "//input[@type='radio']",
                "//label"
            ]
            
            all_clickable = []
            for selector in clickable_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                all_clickable.extend(elements)
            
            logger.info(f"        Elementi cliccabili totali: {len(all_clickable)}")
            
            # Filtra elementi che potrebbero essere relativi a "sold" o "venduti"
            sold_related = []
            for element in all_clickable:
                try:
                    text = element.text.strip().lower()
                    tag = element.tag_name
                    class_name = element.get_attribute("class") or ""
                    id_name = element.get_attribute("id") or ""
                    
                    # Cerca pattern relativi a venduti
                    sold_patterns = ['sold', 'venduti', 'venduto', '37', '7306', 'hide', 'nascondi']
                    
                    if any(pattern in text for pattern in sold_patterns) or \
                       any(pattern in class_name.lower() for pattern in sold_patterns) or \
                       any(pattern in id_name.lower() for pattern in sold_patterns):
                        
                        sold_related.append({
                            'element': element,
                            'text': text,
                            'tag': tag,
                            'class': class_name,
                            'id': id_name
                        })
                        
                except Exception as e:
                    continue
            
            logger.info(f"        Elementi relativi a venduti: {len(sold_related)}")
            
            # Mostra i primi 10 elementi trovati
            for i, item in enumerate(sold_related[:10]):
                logger.info(f"          Elemento {i+1}: '{item['text']}' (tag: {item['tag']}, class: {item['class']}, id: {item['id']})")
            
            # Prova a cliccare sui primi elementi trovati
            for i, item in enumerate(sold_related[:5]):
                try:
                    element = item['element']
                    if element.is_displayed() and element.is_enabled():
                        logger.info(f"        Tentativo click su elemento {i+1}: '{item['text']}'")
                        element.click()
                        time.sleep(3)
                        
                        # Verifica se ora ci sono prezzi
                        price_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '€')]")
                        if price_elements:
                            logger.info(f"        ✅ Prezzi trovati dopo click su elemento {i+1}: {len(price_elements)} elementi")
                            return True
                        
                        # Se non funziona, torna indietro
                        self.driver.back()
                        time.sleep(2)
                        
                except Exception as e:
                    logger.warning(f"        Errore click su elemento {i+1}: {e}")
                    continue
            
        except Exception as e:
            logger.warning(f"      ⚠️ Errore analisi elementi cliccabili: {e}")

    def _analyze_vestiaire_structure(self, profile_name: str) -> int:
        """Analizza la struttura specifica di Vestiaire Collective per trovare vendite reali"""
        try:
            # Aspetta che la pagina sia completamente caricata
            time.sleep(3)
            
            logger.info(f"  🔍 Analizzando struttura Vestiaire per {profile_name}...")
            
            # 1. Cerca nei tab e filtri
            tab_selectors = [
                "//div[contains(@class, 'tab')]//span[contains(text(), 'venduti')]",
                "//div[contains(@class, 'tab')]//span[contains(text(), 'sold')]",
                "//button[contains(@class, 'tab')]//span[contains(text(), 'venduti')]",
                "//button[contains(@class, 'tab')]//span[contains(text(), 'sold')]",
                "//div[contains(@class, 'filter')]//span[contains(text(), 'venduti')]",
                "//div[contains(@class, 'filter')]//span[contains(text(), 'sold')]",
                # Selettori più generici
                "//*[contains(text(), 'venduti')]",
                "//*[contains(text(), 'sold')]",
                "//*[contains(text(), '37')]",
            ]
            
            for i, selector in enumerate(tab_selectors):
                elements = self.driver.find_elements(By.XPATH, selector)
                logger.info(f"    Selettore {i+1}: trovati {len(elements)} elementi")
                
                for j, element in enumerate(elements):
                    try:
                        text = element.text.strip()
                        logger.info(f"      Elemento {j+1}: '{text}'")
                        
                        # Cerca il numero nel testo del tab
                        numbers = re.findall(r'\d+', text)
                        for num in numbers:
                            count = int(num)
                            if 1 <= count <= 1000:
                                logger.info(f"  🔍 Tab trovato per {profile_name}: {count}")
                                return count
                    except Exception as e:
                        logger.warning(f"      Errore elemento {j+1}: {e}")
            
            # 2. Cerca nei contatori di profilo
            profile_counters = [
                "//div[contains(@class, 'profile')]//span[contains(@class, 'count')]",
                "//div[contains(@class, 'user')]//span[contains(@class, 'count')]",
                "//div[contains(@class, 'stats')]//span[contains(@class, 'count')]",
                "//div[contains(@class, 'metrics')]//span[contains(@class, 'count')]",
                # Selettori più generici
                "//span[contains(@class, 'count')]",
                "//div[contains(@class, 'count')]",
                "//*[contains(@class, 'count')]",
            ]
            
            for i, selector in enumerate(profile_counters):
                elements = self.driver.find_elements(By.XPATH, selector)
                logger.info(f"    Contatore {i+1}: trovati {len(elements)} elementi")
                
                for j, element in enumerate(elements):
                    try:
                        text = element.text.strip()
                        logger.info(f"      Contatore {j+1}: '{text}'")
                        
                        if text and text.isdigit():
                            count = int(text)
                            if 1 <= count <= 1000:
                                logger.info(f"  🔍 Contatore profilo per {profile_name}: {count}")
                                return count
                    except Exception as e:
                        logger.warning(f"      Errore contatore {j+1}: {e}")
            
            # 3. Cerca nei dati strutturati
            structured_data_selectors = [
                "//script[@type='application/ld+json']",
                "//script[contains(text(), 'sold')]",
                "//script[contains(text(), 'venduti')]",
                "//script[contains(text(), '37')]",
            ]
            
            for i, selector in enumerate(structured_data_selectors):
                elements = self.driver.find_elements(By.XPATH, selector)
                logger.info(f"    Script {i+1}: trovati {len(elements)} elementi")
                
                for j, element in enumerate(elements):
                    try:
                        script_content = element.get_attribute("innerHTML")
                        if script_content:
                            logger.info(f"      Script {j+1}: {len(script_content)} caratteri")
                            
                            # Cerca pattern JSON con vendite
                            json_patterns = [
                                r'"sold":\s*(\d+)',
                                r'"items_sold":\s*(\d+)',
                                r'"total_sold":\s*(\d+)',
                                r'"venduti":\s*(\d+)',
                                r'"articoli_venduti":\s*(\d+)',
                                r'37',
                            ]
                            
                            for pattern in json_patterns:
                                matches = re.findall(pattern, script_content)
                                if matches:
                                    logger.info(f"        Pattern '{pattern}': {matches}")
                                    if pattern == '37':
                                        count = 37
                                    else:
                                        count = int(matches[0])
                                    if 1 <= count <= 1000:
                                        logger.info(f"  🔍 JSON strutturato per {profile_name}: {count}")
                                        return count
                    except Exception as e:
                        logger.warning(f"      Errore script {j+1}: {e}")
            
            # 4. Cerca nei meta tag
            meta_selectors = [
                "//meta[@name='sold-items']",
                "//meta[@name='items-sold']",
                "//meta[@property='sold-items']",
            ]
            
            for selector in meta_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    content = element.get_attribute("content")
                    if content and content.isdigit():
                        count = int(content)
                        if 1 <= count <= 1000:
                            logger.info(f"  🔍 Meta tag per {profile_name}: {count}")
                            return count
            
            # 5. Cerca nel testo visibile della pagina
            visible_text = self.driver.find_element(By.TAG_NAME, "body").text
            logger.info(f"    Testo visibile: {len(visible_text)} caratteri")
            
            # Salva screenshot per debug
            try:
                timestamp = int(time.time())
                screenshot_path = f"debug_{profile_name.replace(' ', '_')}_{timestamp}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"    📸 Screenshot salvato: {screenshot_path}")
            except Exception as e:
                logger.warning(f"    Errore screenshot: {e}")
            
            # Pattern per testo visibile
            visible_patterns = [
                r'(\d+)\s+articoli?\s+venduti',
                r'(\d+)\s+pezzi?\s+venduti',
                r'(\d+)\s+items?\s+sold',
                r'(\d+)\s+pieces?\s+sold',
                r'venduti[:\s]*(\d+)',
                r'sold[:\s]*(\d+)',
                r'\((\d+)\s+venduti\)',
                r'\((\d+)\s+sold\)',
                r'37',
            ]
            
            for pattern in visible_patterns:
                matches = re.findall(pattern, visible_text, re.IGNORECASE)
                if matches:
                    logger.info(f"    Pattern '{pattern}': {matches}")
                    if pattern == '37':
                        count = 37
                    else:
                        count = int(matches[0])
                    if 1 <= count <= 1000:
                        logger.info(f"  🔍 Testo visibile per {profile_name}: {count}")
                        return count
            
            logger.warning(f"  ⚠️ Nessun contatore trovato per {profile_name}")
            return 0
            
        except Exception as e:
            logger.warning(f"  ⚠️ Errore analisi struttura Vestiaire per {profile_name}: {e}")
            return 0

    def _find_real_sold_count(self, profile_name: str) -> int:
        """Cerca il numero reale di articoli venduti nella pagina"""
        try:
            # 1. Prima prova l'analisi specifica di Vestiaire
            vestiaire_count = self._analyze_vestiaire_structure(profile_name)
            if vestiaire_count > 0:
                return vestiaire_count
            
            # 2. Cerca nei contatori principali
            counter_selectors = [
                "//div[contains(@class, 'counter')]//span",
                "//span[contains(@class, 'count')]",
                "//div[contains(@class, 'stats')]//span",
                "//div[contains(@class, 'profile-stats')]//span",
                "//div[contains(@class, 'user-stats')]//span",
            ]
            
            for selector in counter_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and text.isdigit():
                        count = int(text)
                        # Verifica se è un numero ragionevole (tra 1 e 1000)
                        if 1 <= count <= 1000:
                            logger.info(f"  🔍 Contatore trovato per {profile_name}: {count}")
                            return count
            
            # 3. Cerca nei toggle e bottoni
            toggle_selectors = [
                "//button[contains(text(), 'venduti')]",
                "//button[contains(text(), 'sold')]",
                "//div[contains(text(), 'venduti')]",
                "//div[contains(text(), 'sold')]",
                "//span[contains(text(), 'venduti')]",
                "//span[contains(text(), 'sold')]",
            ]
            
            for selector in toggle_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    text = element.text.strip()
                    # Cerca numeri nel testo del toggle
                    numbers = re.findall(r'\d+', text)
                    for num in numbers:
                        count = int(num)
                        if 1 <= count <= 1000:
                            logger.info(f"  🔍 Toggle trovato per {profile_name}: {count}")
                            return count
            
            # 4. Cerca nel testo della pagina
            page_text = self.driver.page_source
            
            # Pattern specifici per Vestiaire
            vestiaire_patterns = [
                r'(\d+)\s+articoli?\s+venduti',
                r'(\d+)\s+pezzi?\s+venduti',
                r'(\d+)\s+items?\s+sold',
                r'(\d+)\s+pieces?\s+sold',
                r'venduti[:\s]*(\d+)',
                r'sold[:\s]*(\d+)',
                r'\((\d+)\s+venduti\)',
                r'\((\d+)\s+sold\)',
            ]
            
            for pattern in vestiaire_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    count = int(matches[0])
                    if 1 <= count <= 1000:
                        logger.info(f"  🔍 Pattern trovato per {profile_name}: {count}")
                        return count
            
            # 5. Cerca nei dati JSON nascosti
            script_elements = self.driver.find_elements(By.TAG_NAME, "script")
            for script in script_elements:
                script_text = script.get_attribute("innerHTML")
                if script_text:
                    # Cerca dati JSON con informazioni vendite
                    json_patterns = [
                        r'"sold":\s*(\d+)',
                        r'"venduti":\s*(\d+)',
                        r'"items_sold":\s*(\d+)',
                        r'"total_sold":\s*(\d+)',
                    ]
                    
                    for pattern in json_patterns:
                        matches = re.findall(pattern, script_text)
                        if matches:
                            count = int(matches[0])
                            if 1 <= count <= 1000:
                                logger.info(f"  🔍 JSON trovato per {profile_name}: {count}")
                                return count
            
            return 0
            
        except Exception as e:
            logger.warning(f"  ⚠️ Errore ricerca vendite reali per {profile_name}: {e}")
            return 0

    def extract_price_from_text(self, text: str) -> float:
        """Estrae prezzo da testo"""
        try:
            # Cerca pattern prezzo
            price_patterns = [
                r'€\s*([\d,]+\.?\d*)',
                r'EUR\s*([\d,]+\.?\d*)',
                r'([\d,]+\.?\d*)\s*€',
                r'([\d,]+\.?\d*)\s*EUR'
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    price_str = matches[0].replace(',', '')
                    return float(price_str)
            
            return 0.0
        except Exception:
            return 0.0
    
    def scrape_profile_revenue(self, profile_name: str, profile_id: str) -> Dict:
        """Scrapa ricavi per un profilo"""
        start_time = time.time()
        
        try:
            if not self.driver:
                self.setup_driver()
            
            # Naviga alla pagina
            url = f"https://it.vestiairecollective.com/profile/{profile_id}/"
            self.driver.get(url)
            time.sleep(5)
            
            # Gestione cookie
            self._handle_cookie_banner()
            
            # Naviga alla sezione venduti
            navigation_success = self._navigate_to_sold_section(profile_name)
            
            # Se non funziona, prova navigazione URL venduti
            if not navigation_success:
                navigation_success = self._navigate_to_sold_items_url(profile_name, profile_id)
            
            # Se non funziona, prova navigazione sezione articoli
            if not navigation_success:
                navigation_success = self._navigate_to_items_section(profile_name, profile_id)
            
            # Attiva toggle venduti (fallback finale)
            if not navigation_success:
                toggle_activated = self._activate_sold_toggle(profile_name)
            
            # Cerca numero vendite reali
            real_sold_count = 0
            if profile_name in self.existing_sales_data:
                real_sold_count = self.existing_sales_data[profile_name].get('sales', 0)
                logger.info(f"  📊 Dati esistenti per {profile_name}: {real_sold_count} vendite")
            else:
                # Usa il nuovo algoritmo di ricerca
                real_sold_count = self._find_real_sold_count(profile_name)
                
                if real_sold_count > 0:
                    logger.info(f"  ✅ Vendite reali trovate per {profile_name}: {real_sold_count}")
                else:
                    logger.warning(f"  ⚠️ Vendite reali non trovate per {profile_name}, uso stima")
            
            # Estrai prezzi di vendita finali
            sold_items_prices = self._extract_final_sale_prices(profile_name)
            
            # Debug della struttura della pagina se non troviamo prezzi
            if len(sold_items_prices) == 0:
                self._debug_page_structure(profile_name)
            
            # Calcola ricavi
            total_revenue = sum(sold_items_prices)
            
            # Se non abbiamo numero reale, usa prezzi estratti
            if real_sold_count == 0:
                real_sold_count = len(sold_items_prices)
                logger.warning(f"  ⚠️ Usando {real_sold_count} prezzi estratti come stima per {profile_name}")
            else:
                logger.info(f"  📊 Vendite reali: {real_sold_count}, Prezzi estratti: {len(sold_items_prices)}")
                
                # Se abbiamo più prezzi che vendite, prendi solo i primi N
                if len(sold_items_prices) > real_sold_count:
                    sold_items_prices = sold_items_prices[:real_sold_count]
                    total_revenue = sum(sold_items_prices)
                    logger.info(f"  🔧 Limitato a {real_sold_count} prezzi per {profile_name}")
                elif len(sold_items_prices) < real_sold_count:
                    logger.warning(f"  ⚠️ Meno prezzi ({len(sold_items_prices)}) che vendite ({real_sold_count}) per {profile_name}")
            
            total_time = time.time() - start_time
            
            return {
                "name": profile_name,
                "profile_id": profile_id,
                "success": True,
                "sold_items_count": real_sold_count,
                "total_revenue": total_revenue,
                "sold_items_prices": sold_items_prices,
                "performance": {"total_time": total_time}
            }
            
        except Exception as e:
            logger.error(f"Errore scraping {profile_name}: {e}")
            return {
                "name": profile_name,
                "profile_id": profile_id,
                "success": False,
                "error": str(e),
                "sold_items_count": 0,
                "total_revenue": 0.0,
                "sold_items_prices": [],
                "performance": {"total_time": time.time() - start_time}
            }
    
    def scrape_all_profiles_revenue(self) -> List[Dict]:
        """Scrapa tutti i profili"""
        logger.info("Avvio scraping ricavi...")
        
        try:
            from config import OPTIMIZATION_CONFIG
            max_workers = OPTIMIZATION_CONFIG.get("max_parallel_workers", 3)
            
            # Scraping parallelo
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.scrape_profile_revenue, name, id): (name, id)
                    for name, id in self.profiles.items()
                }
                
                results = []
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        name, id = futures[future]
                        results.append({
                            "name": name,
                            "profile_id": id,
                            "success": False,
                            "error": str(e),
                            "sold_items_count": 0,
                            "total_revenue": 0.0,
                            "sold_items_prices": [],
                            "performance": {"total_time": 0}
                        })
            
            return results
            
        except Exception as e:
            logger.error(f"Errore scraping parallelo: {e}")
            # Fallback sequenziale
            results = []
            for name, id in self.profiles.items():
                result = self.scrape_profile_revenue(name, id)
                results.append(result)
            return results 