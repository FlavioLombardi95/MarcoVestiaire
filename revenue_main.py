#!/usr/bin/env python3
"""
Revenue Monitor - Sistema parallelo per analisi ricavi
Sistema di monitoraggio automatico dei ricavi dai profili Vendors su Vestiaire Collective
"""

import sys
import os
import logging
from datetime import datetime
import traceback
from typing import List, Dict
import json

# Aggiungi il percorso corrente al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from revenue_scraper import RevenueScraper
from revenue_sheets_updater import RevenueSheetsUpdater

# Import configurazione dalla root directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import VESTIAIRE_PROFILES as PROFILES

# Configurazione logging
def setup_logging():
    """Configura il logging con file e console"""
    # Crea le directory logs se non esistono
    os.makedirs('logs', exist_ok=True)
    os.makedirs('../logs', exist_ok=True)  # Per GitHub Actions
    
    # Nome file con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f'logs/revenue_monitor_{timestamp}.log'
    
    # Configurazione logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Rimuovi handler esistenti
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Formatter dettagliato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handler per file in src/logs/
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler per console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Log nella root directory per GitHub Actions
    try:
        root_log = '../revenue_monitor.log'
        root_handler = logging.FileHandler(root_log, encoding='utf-8')
        root_handler.setLevel(logging.INFO)
        root_handler.setFormatter(formatter)
        logger.addHandler(root_handler)
    except:
        # Se fallisce, prova nella directory corrente
        root_log = 'revenue_monitor.log'
        root_handler = logging.FileHandler(root_log, encoding='utf-8')
        root_handler.setLevel(logging.INFO)
        root_handler.setFormatter(formatter)
        logger.addHandler(root_handler)
    
    return logger

logger = setup_logging()

def load_credentials() -> Dict:
    """Carica le credenziali Google Sheets automaticamente"""
    try:
        # Prova a caricare da variabile d'ambiente
        credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
        if credentials_json:
            return json.loads(credentials_json)
        
        # Prova a caricare da variabile d'ambiente con percorso file
        credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE')
        if credentials_file and os.path.exists(credentials_file):
            with open(credentials_file, 'r') as f:
                return json.load(f)
        
        # Cerca automaticamente il file delle credenziali nella directory del progetto
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        possible_files = [
            "vestiaire-monitor-ba3e8b6417eb.json",
            "credentials.json",
            "google-sheets-credentials.json"
        ]
        
        for filename in possible_files:
            file_path = os.path.join(project_root, filename)
            if os.path.exists(file_path):
                logger.info(f"Caricamento credenziali da: {file_path}")
                with open(file_path, 'r') as f:
                    return json.load(f)
        
        logger.warning("Nessuna credenziale trovata. Lo scraping funzionerà ma non l'aggiornamento di Google Sheets.")
        return {}
        
    except Exception as e:
        logger.error(f"Errore nel caricamento delle credenziali: {e}")
        return {}

def save_debug_data(data: Dict, filename: str):
    """Salva dati di debug in formato JSON"""
    try:
        os.makedirs('logs', exist_ok=True)
        os.makedirs('../logs', exist_ok=True)  # Per GitHub Actions
        
        # Salva in src/logs/
        filepath = f'logs/{filename}'
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Salva anche nella root per GitHub Actions
        try:
            root_filepath = f'../{filename}'
            with open(root_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"📝 Dati di debug salvati in {filepath} e {root_filepath}")
        except:
            logger.info(f"📝 Dati di debug salvati in {filepath}")
            
    except Exception as e:
        logger.error(f"❌ Errore nel salvataggio debug: {e}")

def main():
    """Funzione principale per l'analisi dei ricavi"""
    try:
        logger.info("💰 AVVIO REVENUE MONITOR")
        logger.info("=" * 50)
        
        # Gestione parametri
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == "test":
                return test_revenue_scraping()
            elif command == "performance":
                return test_revenue_performance()
            elif command == "test-sheets":
                return test_revenue_sheets()
            elif command == "help":
                print("💰 REVENUE MONITOR - Comandi disponibili:")
                print("  python revenue_main.py              - Esecuzione normale")
                print("  python revenue_main.py test         - Test revenue scraping")
                print("  python revenue_main.py performance  - Test performance revenue")
                print("  python revenue_main.py test-sheets  - Test Google Sheets revenue")
                print("  python revenue_main.py help         - Mostra questo help")
                return True
            else:
                logger.error(f"❌ Comando '{command}' non riconosciuto. Usa 'help' per vedere i comandi disponibili.")
                return False
        
        # Esecuzione normale
        logger.info("🔧 Controllo configurazione ambiente...")
        
        # Verifica credenziali
        credentials_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
        if not credentials_json:
            logger.error("❌ Credenziali Google Sheets non trovate")
            return False
        
        logger.info("✅ Credenziali Google Sheets trovate")
        
        # Test connessione Google Sheets
        logger.info("🔍 Test connessione Google Sheets...")
        try:
            updater = RevenueSheetsUpdater(credentials_json)
            if not updater.service:
                logger.error("❌ Impossibile configurare il servizio Google Sheets")
                return False
            logger.info("✅ Connessione Google Sheets OK")
        except Exception as e:
            logger.error(f"❌ Errore nella connessione Google Sheets: {e}")
            return False
        
        # Prima otteniamo i dati esistenti dal sistema principale per avere i numeri reali di vendite
        logger.info("🔍 Ottenimento dati vendite esistenti...")
        try:
            # Importa il sistema principale
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            
            from scraper import VestiaireScraper
            main_scraper = VestiaireScraper(profiles=PROFILES)
            existing_data = main_scraper.scrape_all_profiles()
            
            # Converti in formato utilizzabile
            existing_sales_data = {}
            for profile in existing_data:
                if profile.get('success', False):
                    existing_sales_data[profile['name']] = {
                        'sales': profile.get('sales', 0),
                        'articles': profile.get('articles', 0)
                    }
            
            logger.info(f"✅ Dati esistenti ottenuti per {len(existing_sales_data)} profili")
            for name, data in existing_sales_data.items():
                logger.info(f"  📊 {name}: {data['sales']} vendite, {data['articles']} articoli")
            
        except Exception as e:
            logger.warning(f"⚠️ Impossibile ottenere dati esistenti: {e}")
            existing_sales_data = {}
        
        # Inizializza revenue scraper con i dati esistenti
        logger.info("🔍 Inizializzazione revenue scraper...")
        
        # Carica configurazione per processing parallelo
        from config import OPTIMIZATION_CONFIG
        max_workers = OPTIMIZATION_CONFIG.get("max_parallel_workers", 3)
        parallel_enabled = OPTIMIZATION_CONFIG.get("parallel_scraping", True)
        
        logger.info(f"⚡ Configurazione parallelo: {max_workers} workers, abilitato: {parallel_enabled}")
        
        scraper = RevenueScraper(profiles=PROFILES, existing_sales_data=existing_sales_data)
        
        # Scraping dei dati ricavi
        logger.info("💰 Avvio scraping ricavi dei profili...")
        logger.info(f"📋 Profili da processare: {len(PROFILES)}")
        
        scraped_data = scraper.scrape_all_profiles_revenue()
        
        # Salva dati di debug
        debug_data = {
            'timestamp': datetime.now().isoformat(),
            'total_profiles': len(PROFILES),
            'scraped_profiles': len(scraped_data) if scraped_data else 0,
            'scraped_data': scraped_data if scraped_data else []
        }
        save_debug_data(debug_data, f'revenue_scraping_debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        
        if not scraped_data:
            logger.error("❌ Nessun dato ricavi recuperato dallo scraping")
            logger.error("💡 Possibili cause: rete, rate limiting, modifiche siti web")
            return False
        
        logger.info(f"✅ Scraping ricavi completato: {len(scraped_data)} profili processati")
        
        # Log dettagliato dei dati ricavi
        logger.info("💰 DATI RICAVI RACCOLTI:")
        total_items = 0
        total_revenue = 0.0
        
        for profile in scraped_data:
            items = profile.get('sold_items_count', 0)
            revenue = profile.get('total_revenue', 0.0)
            total_items += items
            total_revenue += revenue
            logger.info(f"  📍 {profile.get('name', 'Unknown')}: {items} articoli venduti, €{revenue:.2f} ricavi")
        
        logger.info(f"💰 TOTALI: {total_items} articoli venduti, €{total_revenue:.2f} ricavi totali")
        
        # Aggiorna Google Sheets
        logger.info("📝 Aggiornamento Google Sheets ricavi...")
        
        # Aggiorna il foglio mensile ricavi
        now = datetime.now()
        logger.info(f"📅 Aggiornamento ricavi per: {now.day}/{now.month}/{now.year}")
        
        success = updater.update_revenue_monthly_sheet(scraped_data, now.year, now.month, now.day)
        
        if success:
            logger.info("✅ Aggiornamento Google Sheets ricavi completato")
            logger.info("🎯 Operazione ricavi completata con successo!")
            return True
        else:
            logger.error("❌ Errore nell'aggiornamento Google Sheets ricavi")
            return False
            
    except Exception as e:
        logger.error(f"❌ Errore durante l'esecuzione revenue monitor: {e}")
        logger.error(f"📍 Traceback: {traceback.format_exc()}")
        return False

def test_revenue_scraping():
    """Funzione di test per lo scraping ricavi"""
    logger.info("=== TEST REVENUE SCRAPING ===")
    
    try:
        # Prima otteniamo i dati esistenti dal sistema principale
        logger.info("🔍 Ottenimento dati vendite esistenti...")
        try:
            # Importa il sistema principale
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            
            from scraper import VestiaireScraper
            main_scraper = VestiaireScraper(profiles=PROFILES)
            existing_data = main_scraper.scrape_all_profiles()
            
            # Converti in formato utilizzabile
            existing_sales_data = {}
            for profile in existing_data:
                if profile.get('success', False):
                    existing_sales_data[profile['name']] = {
                        'sales': profile.get('sales', 0),
                        'articles': profile.get('articles', 0)
                    }
            
            logger.info(f"✅ Dati esistenti ottenuti per {len(existing_sales_data)} profili")
            for name, data in existing_sales_data.items():
                logger.info(f"  📊 {name}: {data['sales']} vendite, {data['articles']} articoli")
            
        except Exception as e:
            logger.warning(f"⚠️ Impossibile ottenere dati esistenti: {e}")
            existing_sales_data = {}
        
        # Inizializza revenue scraper con i dati esistenti
        scraper = RevenueScraper(profiles=PROFILES, existing_sales_data=existing_sales_data)
        results = scraper.scrape_all_profiles_revenue()
        
        print("\n=== RISULTATI TEST REVENUE ===")
        for result in results:
            print(f"{result['name']}: {result['sold_items_count']} articoli venduti, €{result['total_revenue']:.2f} ricavi")
        
        totals = scraper.calculate_revenue_totals(results)
        print(f"\nTOTALI: {totals['total_sold_items']} articoli venduti, €{totals['total_revenue']:.2f} ricavi totali")
        
        return True
        
    except Exception as e:
        logger.error(f"Errore nel test revenue: {e}")
        return False

def test_revenue_performance():
    """Funzione specifica per testare le performance dello scraping ricavi"""
    logger.info("=== TEST PERFORMANCE REVENUE SCRAPING ===")
    
    try:
        scraper = RevenueScraper()
        
        # Esegui lo scraping con monitoraggio completo
        results = scraper.scrape_all_profiles_revenue()
        
        # Ottieni statistiche dettagliate
        stats = scraper.get_performance_stats()
        
        print("\n" + "="*70)
        print("💰 ANALISI PERFORMANCE REVENUE DETTAGLIATA")
        print("="*70)
        
        # Benchmark generale
        print("⚡ BENCHMARK GENERALE:")
        print(f"   Setup driver: {stats['driver_setup_time']:.2f}s")
        print(f"   Scraping totale: {stats['total_scraping_time']:.2f}s")
        print(f"   Tempo medio per profilo: {stats['average_profile_time']:.2f}s")
        print(f"   Profili per minuto: {60 / stats['average_profile_time']:.1f}")
        
        # Analisi velocità
        print("\n🏆 ANALISI VELOCITÀ:")
        print(f"   Più veloce: {stats['fastest_profile']['name']} ({stats['fastest_profile']['time']:.2f}s)")
        print(f"   Più lento: {stats['slowest_profile']['name']} ({stats['slowest_profile']['time']:.2f}s)")
        
        # Confronto con soglie di performance
        print("\n📊 VALUTAZIONE PERFORMANCE:")
        avg_time = stats['average_profile_time']
        if avg_time < 8:
            performance_rating = "🟢 ECCELLENTE"
        elif avg_time < 12:
            performance_rating = "🟡 BUONA"
        else:
            performance_rating = "🔴 LENTA"
        print(f"   Rating: {performance_rating}")
        
        # Suggerimenti di ottimizzazione
        print("\n💡 SUGGERIMENTI OTTIMIZZAZIONE:")
        total_wait_time = (len(scraper.profiles) - 1) * 3
        active_work_time = stats['total_scraping_time'] - total_wait_time
        efficiency = (active_work_time / stats['total_scraping_time']) * 100
        
        print(f"   Efficienza attuale: {efficiency:.1f}%")
        if efficiency < 50:
            print("   ⚠️  Considerare riduzione tempi di attesa")
        if avg_time > 10:
            print("   ⚠️  Considerare ottimizzazione parsing HTML")
        
        # Test di velocità di rete
        print("\n🌐 TEST VELOCITÀ RETE:")
        fastest_load = min(data['page_load_time'] for data in stats['profile_times'].values())
        slowest_load = max(data['page_load_time'] for data in stats['profile_times'].values())
        avg_load = sum(data['page_load_time'] for data in stats['profile_times'].values()) / len(stats['profile_times'])
        
        print(f"   Caricamento più veloce: {fastest_load:.2f}s")
        print(f"   Caricamento più lento: {slowest_load:.2f}s")
        print(f"   Caricamento medio: {avg_load:.2f}s")
        
        if avg_load > 7:
            print("   ⚠️  Connessione lenta rilevata")
        
        # Proiezioni per diversi scenari
        print("\n📈 PROIEZIONI SCALABILITÀ:")
        profiles_per_hour = 3600 / (stats['average_profile_time'] + 3)  # +3 per pausa
        print(f"   Profili processabili per ora: {profiles_per_hour:.0f}")
        print(f"   Tempo per 100 profili: {(100 * (stats['average_profile_time'] + 3)) / 60:.1f} minuti")
        
        print("="*70)
        
        return True
        
    except Exception as e:
        logger.error(f"Errore nel test performance revenue: {e}")
        return False

def test_revenue_sheets():
    """Funzione di test per Google Sheets ricavi"""
    logger.info("=== TEST GOOGLE SHEETS REVENUE ===")
    
    try:
        credentials = load_credentials()
        if not credentials:
            logger.error("Nessuna credenziale trovata per il test")
            return False
        
        # Test con dati fittizi
        test_data = [
            {
                "name": "Test Profile", 
                "url": "https://example.com", 
                "sold_items_count": 10, 
                "total_revenue": 1500.50, 
                "timestamp": "2024-01-01 12:00:00"
            }
        ]
        
        import json as _json
        if isinstance(credentials, dict):
            credentials_json = _json.dumps(credentials)
        else:
            credentials_json = credentials
            
        sheets_updater = RevenueSheetsUpdater(credentials_json)
        
        # Test per il mese corrente
        now = datetime.now()
        success = sheets_updater.update_revenue_monthly_sheet(test_data, now.year, now.month, now.day)
        
        if success:
            logger.info("Test Google Sheets revenue completato con successo")
        else:
            logger.error("Test Google Sheets revenue fallito")
        return success
    except Exception as e:
        logger.error(f"Errore nel test Google Sheets revenue: {e}")
        return False

if __name__ == "__main__":
    # Controlla gli argomenti della riga di comando
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "test":
            test_revenue_scraping()
        elif command == "performance":
            test_revenue_performance()
        elif command == "test-sheets":
            test_revenue_sheets()
        elif command == "help":
            print("Comandi disponibili:")
            print("  python revenue_main.py              - Esegue il monitoraggio ricavi completo")
            print("  python revenue_main.py test         - Testa solo lo scraping ricavi")
            print("  python revenue_main.py performance  - Test dettagliato delle performance revenue")
            print("  python revenue_main.py test-sheets  - Testa solo Google Sheets revenue")
            print("  python revenue_main.py help         - Mostra questo aiuto")
        else:
            print(f"Comando sconosciuto: {command}")
            print("Usa 'python revenue_main.py help' per vedere i comandi disponibili")
    else:
        # Esegui il monitoraggio ricavi completo
        main() 