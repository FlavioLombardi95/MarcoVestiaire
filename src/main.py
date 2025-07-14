#!/usr/bin/env python3
"""
Vestiaire Monitor - Sistema di monitoraggio automatico
Aggiornato con debugging avanzato e sistema di performance monitoring
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

from scraper import VestiaireScraper
from sheets_updater import GoogleSheetsUpdater
from config import PROFILES, PERFORMANCE_THRESHOLDS
from credentials_test import CredentialsTest

# Configurazione logging migliorata
def setup_logging():
    """Configura il logging con file e console"""
    # Crea le directory logs se non esistono
    os.makedirs('logs', exist_ok=True)
    os.makedirs('../logs', exist_ok=True)  # Per GitHub Actions
    
    # Nome file con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f'logs/vestiaire_monitor_{timestamp}.log'
    
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
        root_log = '../vestiaire_monitor.log'
        root_handler = logging.FileHandler(root_log, encoding='utf-8')
        root_handler.setLevel(logging.INFO)
        root_handler.setFormatter(formatter)
        logger.addHandler(root_handler)
    except:
        # Se fallisce, prova nella directory corrente
        root_log = 'vestiaire_monitor.log'
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
    """Funzione principale con gestione parametri"""
    try:
        logger.info("🚀 AVVIO VESTIAIRE MONITOR")
        logger.info("=" * 50)
        
        # Gestione parametri
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == "performance":
                return test_performance()
            elif command == "debug-scraping":
                return debug_scraping_issue()
            elif command == "debug-totali":
                return debug_totals()
            elif command == "test-credentials":
                return test_credentials()
            elif command == "help":
                print("🚀 VESTIAIRE MONITOR - Comandi disponibili:")
                print("  python main.py                  - Esecuzione normale")
                print("  python main.py performance      - Test performance")
                print("  python main.py debug-scraping   - Debug scraping")
                print("  python main.py debug-totali     - Debug calcoli totali")
                print("  python main.py test-credentials - Test credenziali Google Sheets")
                print("  python main.py help             - Mostra questo help")
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
            updater = GoogleSheetsUpdater(credentials_json)
            if not updater.service:
                logger.error("❌ Impossibile configurare il servizio Google Sheets")
                return False
            logger.info("✅ Connessione Google Sheets OK")
        except Exception as e:
            logger.error(f"❌ Errore nella connessione Google Sheets: {e}")
            return False
        
        # Inizializza scraper
        logger.info("🔍 Inizializzazione scraper...")
        scraper = VestiaireScraper()
        
        # Scraping dei dati
        logger.info("📡 Avvio scraping dei profili...")
        logger.info(f"📋 Profili da processare: {len(PROFILES)}")
        
        scraped_data = scraper.scrape_all_profiles()
        
        # Salva dati di debug
        debug_data = {
            'timestamp': datetime.now().isoformat(),
            'total_profiles': len(PROFILES),
            'scraped_profiles': len(scraped_data) if scraped_data else 0,
            'scraped_data': scraped_data if scraped_data else []
        }
        save_debug_data(debug_data, f'scraping_debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        
        if not scraped_data:
            logger.error("❌ Nessun dato recuperato dallo scraping")
            logger.error("💡 Possibili cause: rete, rate limiting, modifiche siti web")
            return False
        
        logger.info(f"✅ Scraping completato: {len(scraped_data)} profili processati")
        
        # Log dettagliato dei dati
        logger.info("📊 DATI RACCOLTI:")
        total_articles = 0
        total_sales = 0
        
        for profile in scraped_data:
            articles = profile.get('articles', 0)
            sales = profile.get('sales', 0)
            total_articles += articles
            total_sales += sales
            logger.info(f"  📍 {profile.get('name', 'Unknown')}: {articles} articoli, {sales} vendite")
        
        logger.info(f"📈 TOTALI: {total_articles} articoli, {total_sales} vendite")
        
        # Aggiorna Google Sheets
        logger.info("📝 Aggiornamento Google Sheets...")
        # Riutilizza la stessa istanza testata prima
        
        # Aggiorna il foglio mensile
        now = datetime.now()
        logger.info(f"📅 Aggiornamento per: {now.day}/{now.month}/{now.year}")
        
        success = updater.update_monthly_sheet(scraped_data, now.year, now.month, now.day)
        
        if success:
            logger.info("✅ Aggiornamento Google Sheets completato")
            logger.info("🎯 Operazione completata con successo!")
            return True
        else:
            logger.error("❌ Errore nell'aggiornamento Google Sheets")
            return False
            
    except Exception as e:
        logger.error(f"❌ Errore durante l'esecuzione: {e}")
        logger.error(f"📍 Traceback: {traceback.format_exc()}")
        return False

def test_scraping():
    """Funzione di test per lo scraping"""
    logger.info("=== TEST SCRAPING ===")
    
    try:
        scraper = VestiaireScraper()
        results = scraper.scrape_all_profiles()
        
        print("\n=== RISULTATI TEST ===")
        for result in results:
            print(f"{result['name']}: {result['articles']} articoli, {result['sales']} vendite")
        
        totals = scraper.calculate_totals(results)
        print(f"\nTOTALI: {totals['total_articles']} articoli, {totals['total_sales']} vendite")
        
        return True
        
    except Exception as e:
        logger.error(f"Errore nel test: {e}")
        return False

def test_performance():
    """Funzione specifica per testare le performance dello scraping"""
    logger.info("=== TEST PERFORMANCE SCRAPING ===")
    
    try:
        scraper = VestiaireScraper()
        
        # Esegui lo scraping con monitoraggio completo
        results = scraper.scrape_all_profiles()
        
        # Ottieni statistiche dettagliate
        stats = scraper.get_performance_stats()
        
        print("\n" + "="*70)
        print("🚀 ANALISI PERFORMANCE DETTAGLIATA")
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
        logger.error(f"Errore nel test performance: {e}")
        return False

def test_sheets():
    """Funzione di test per Google Sheets"""
    logger.info("=== TEST GOOGLE SHEETS ===")
    
    try:
        credentials = load_credentials()
        if not credentials:
            logger.error("Nessuna credenziale trovata per il test")
            return False
        
        # Test con dati fittizi
        test_data = [
            {"name": "Test Profile", "url": "https://example.com", "articles": 100, "sales": 50, "timestamp": "2024-01-01 12:00:00"}
        ]
        
        import json as _json
        if isinstance(credentials, dict):
            credentials_json = _json.dumps(credentials)
        else:
            credentials_json = credentials
            
        sheets_updater = GoogleSheetsUpdater(credentials_json)
        success = sheets_updater.update_sheet(test_data, sheet_name="riepilogo")
        
        if success:
            logger.info("Test Google Sheets completato con successo")
        else:
            logger.error("Test Google Sheets fallito")
        return success
    except Exception as e:
        logger.error(f"Errore nel test Google Sheets: {e}")
        return False

def aggiorna_sheet_con_dati_statici():
    """Aggiorna la tab 'riepilogo' con i dati statici dell'ultimo test, cancellando prima tutto."""
    logger.info("=== AGGIORNAMENTO SOLO SHEET CON DATI STATICI ===")
    dati = [
        {"name": "Rediscover", "url": "https://it.vestiairecollective.com/profile/2039815/", "articles": 592, "sales": 7217, "timestamp": ""},
        {"name": "Volodymyr", "url": "https://it.vestiairecollective.com/profile/5924329/", "articles": 0, "sales": 0, "timestamp": ""},
        {"name": "stephanie", "url": "https://it.vestiairecollective.com/profile/9168643/", "articles": 565, "sales": 801, "timestamp": ""},
        {"name": "Mark", "url": "https://it.vestiairecollective.com/profile/13442939/", "articles": 5027, "sales": 1891, "timestamp": ""},
        {"name": "A Retro Tale", "url": "https://it.vestiairecollective.com/profile/5537180/", "articles": 5064, "sales": 5433, "timestamp": ""},
        {"name": "Lapsa", "url": "https://it.vestiairecollective.com/profile/11345596/", "articles": 795, "sales": 4349, "timestamp": ""},
        {"name": "Bag", "url": "https://it.vestiairecollective.com/profile/3770739/", "articles": 14, "sales": 230, "timestamp": ""},
        {"name": "Clara", "url": "https://it.vestiairecollective.com/profile/27862876/", "articles": 1610, "sales": 149, "timestamp": ""},
        {"name": "Baggy Vintage", "url": "https://it.vestiairecollective.com/profile/18106856/", "articles": 369, "sales": 675, "timestamp": ""},
        {"name": "Vintageandkickz", "url": "https://it.vestiairecollective.com/profile/19199976/", "articles": 2389, "sales": 4178, "timestamp": ""},
        {"name": "Vintage & Modern", "url": "https://it.vestiairecollective.com/profile/29517320/", "articles": 24, "sales": 27, "timestamp": ""},
    ]
    credentials = load_credentials()
    import json as _json
    if isinstance(credentials, dict):
        credentials_json = _json.dumps(credentials)
    else:
        credentials_json = credentials
    sheets_updater = GoogleSheetsUpdater(credentials_json)
    sheets_updater.update_sheet(dati, sheet_name="riepilogo")
    logger.info("Aggiornamento completato!")

def aggiorna_tab_mensile_statico():
    """Aggiorna la tab mensile con i dati statici dell'ultimo test, usando la nuova logica."""
    import datetime
    logger.info("=== AGGIORNAMENTO TAB MENSILE CON DATI STATICI ===")
    dati = [
        {"name": "Rediscover", "url": "https://it.vestiairecollective.com/profile/2039815/", "articles": 592, "sales": 7217, "timestamp": ""},
        {"name": "Volodymyr", "url": "https://it.vestiairecollective.com/profile/5924329/", "articles": 0, "sales": 0, "timestamp": ""},
        {"name": "stephanie", "url": "https://it.vestiairecollective.com/profile/9168643/", "articles": 565, "sales": 801, "timestamp": ""},
        {"name": "Mark", "url": "https://it.vestiairecollective.com/profile/13442939/", "articles": 5027, "sales": 1891, "timestamp": ""},
        {"name": "A Retro Tale", "url": "https://it.vestiairecollective.com/profile/5537180/", "articles": 5064, "sales": 5433, "timestamp": ""},
        {"name": "Lapsa", "url": "https://it.vestiairecollective.com/profile/11345596/", "articles": 795, "sales": 4349, "timestamp": ""},
        {"name": "Bag", "url": "https://it.vestiairecollective.com/profile/3770739/", "articles": 14, "sales": 230, "timestamp": ""},
        {"name": "Clara", "url": "https://it.vestiairecollective.com/profile/27862876/", "articles": 1610, "sales": 149, "timestamp": ""},
        {"name": "Baggy Vintage", "url": "https://it.vestiairecollective.com/profile/18106856/", "articles": 369, "sales": 675, "timestamp": ""},
        {"name": "Vintageandkickz", "url": "https://it.vestiairecollective.com/profile/19199976/", "articles": 2389, "sales": 4178, "timestamp": ""},
        {"name": "Vintage & Modern", "url": "https://it.vestiairecollective.com/profile/29517320/", "articles": 24, "sales": 27, "timestamp": ""},
    ]
    credentials = load_credentials()
    import json as _json
    if isinstance(credentials, dict):
        credentials_json = _json.dumps(credentials)
    else:
        credentials_json = credentials
    sheets_updater = GoogleSheetsUpdater(credentials_json)
    today = datetime.date.today()
    sheets_updater.update_monthly_sheet(dati, today.year, today.month, today.day)
    logger.info("Aggiornamento tab mensile completato!")

def formatta_tab_mensile():
    import datetime
    logger.info("=== FORMATTAZIONE SOLO TAB MENSILE ===")
    credentials = load_credentials()
    import json as _json
    if isinstance(credentials, dict):
        credentials_json = _json.dumps(credentials)
    else:
        credentials_json = credentials
    sheets_updater = GoogleSheetsUpdater(credentials_json)
    today = datetime.date.today()
    month_name = today.strftime('%B').lower()
    sheets_updater.format_only_monthly_sheet(month_name, today.year)
    logger.info("Formattazione tab mensile completata!")

def debug_scraping_issue():
    """Funzione specifica per debuggare il problema dei dati identici"""
    logger.info("=== DEBUG PROBLEMA DATI IDENTICI ===")
    
    try:
        scraper = VestiaireScraper()
        
        # Test solo su 2-3 profili per velocità
        test_profiles = {
            "Rediscover": "2039815",
            "Volodymyr": "5924329",
            "stephanie": "9168643"
        }
        
        logger.info(f"🔍 Test scraping su {len(test_profiles)} profili...")
        
        results = []
        for profile_name, profile_id in test_profiles.items():
            logger.info(f"\n--- Test profilo: {profile_name} ---")
            result = scraper.scrape_profile(profile_name, profile_id)
            results.append(result)
            
            # Analisi dettagliata del risultato
            success = result.get('success', False)
            articles = result.get('articles', 0)
            sales = result.get('sales', 0)
            error = result.get('error', '')
            data_quality = result.get('data_quality', {})
            
            print(f"✅ Successo: {success}")
            print(f"📦 Articoli: {articles}")
            print(f"💰 Vendite: {sales}")
            if error:
                print(f"❌ Errore: {error}")
            if data_quality:
                print(f"🔍 Qualità dati: {data_quality}")
            
            # Verifica se i dati corrispondono ai valori statici noti
            static_data = {
                "Rediscover": {"articles": 592, "sales": 7217},
                "Volodymyr": {"articles": 0, "sales": 0},
                "stephanie": {"articles": 565, "sales": 801}
            }
            
            if profile_name in static_data:
                expected = static_data[profile_name]
                if articles == expected["articles"] and sales == expected["sales"]:
                    print(f"⚠️  SOSPETTO: Dati identici ai valori statici noti!")
                else:
                    print(f"✅ Dati diversi dai valori statici (buon segno)")
            
            time.sleep(2)  # Pausa tra profili
        
        # Analisi globale
        print("\n" + "="*60)
        print("📊 ANALISI GLOBALE")
        print("="*60)
        
        total_articles = sum(r.get('articles', 0) for r in results)
        total_sales = sum(r.get('sales', 0) for r in results)
        successful_profiles = sum(1 for r in results if r.get('success', False))
        
        print(f"Profili con successo: {successful_profiles}/{len(results)}")
        print(f"Totale articoli: {total_articles}")
        print(f"Totale vendite: {total_sales}")
        
        # Controllo contro dati statici noti (parziali)
        known_partial_totals = {"articles": 1157, "sales": 8018}  # Totali dei 3 profili test
        if total_articles == known_partial_totals["articles"] and total_sales == known_partial_totals["sales"]:
            print("🚨 PROBLEMA CONFERMATO: I dati sono identici ai valori statici!")
            print("   Possibili cause:")
            print("   1. Lo scraping fallisce e restituisce valori di default")
            print("   2. Vestiaire ha modificato la struttura HTML")
            print("   3. Problemi di rete o rate limiting")
        else:
            print("✅ I dati sembrano essere reali (diversi dai valori statici)")
        
        # Test specifico per verificare se il problema è nel calcolo delle differenze
        print(f"\n🔧 TEST CALCOLO DIFFERENZE:")
        print(f"Se questi fossero dati per il giorno 15 luglio:")
        for result in results:
            name = result['name']
            articles = result['articles']
            sales = result['sales']
            
            # Simula i dati del giorno precedente (14 luglio) = stessi valori
            prev_articles = articles  # Stesso valore = diff 0
            prev_sales = sales        # Stesso valore = diff 0
            
            diff_articles = articles - prev_articles
            diff_sales = sales - prev_sales
            
            print(f"  {name}: {articles} articoli (diff: {diff_articles}), {sales} vendite (diff: {diff_sales})")
        
        print("Se tutti i diff sono 0, significa che i dati sono identici al giorno precedente")
        
        return True
        
    except Exception as e:
        logger.error(f"Errore nel debug: {e}")
        return False
    finally:
        if hasattr(scraper, 'driver') and scraper.driver:
            scraper.driver.quit()
            logger.info("Driver chiuso")

def debug_totals():
    """Debug dei calcoli dei totali nelle Google Sheets"""
    try:
        print("🔍 DEBUGGING TOTALI GOOGLE SHEETS")
        print("=" * 50)
        
        # Configura le credenziali
        credentials_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
        if not credentials_json:
            print("❌ ERRORE: Credenziali Google Sheets non trovate")
            return False
            
        # Inizializza l'updater
        updater = GoogleSheetsUpdater(credentials_json)
        
        # Leggi i dati attuali del foglio corrente
        import calendar
        current_month = datetime.now().month
        month_name = calendar.month_name[current_month].lower()
        year = datetime.now().year
        
        print(f"📖 Lettura dati da {month_name} {year}...")
        
        result = updater.service.spreadsheets().values().get(
            spreadsheetId=updater.spreadsheet_id,
            range=f"{month_name}!A:ZZ"
        ).execute()
        
        values = result.get('values', [])
        if not values:
            print(f"❌ ERRORE: Tab {month_name} vuota!")
            return False
            
        header = values[0]
        print(f"📊 Header: {header}")
        print(f"📊 Numero righe: {len(values)}")
        
        # Analizza ogni colonna per i totali
        print("\n🔢 ANALISI COLONNE E TOTALI:")
        print("-" * 40)
        
        for col_idx in range(2, len(header)):
            col_name = header[col_idx] if col_idx < len(header) else f"Col_{col_idx}"
            print(f"\n📋 Colonna {col_idx}: {col_name}")
            
            col_sum = 0
            valid_values = []
            invalid_values = []
            
            # Calcola somma escludendo header e riga totali
            for row_idx in range(1, len(values)):
                row = values[row_idx]
                if row and row[0] == "Totali":
                    continue  # Salta la riga totali
                    
                if col_idx < len(row) and row[col_idx]:
                    cell_value = row[col_idx]
                    try:
                        numeric_val = int(cell_value)
                        col_sum += numeric_val
                        valid_values.append(f"R{row_idx+1}: {numeric_val}")
                    except (ValueError, TypeError):
                        invalid_values.append(f"R{row_idx+1}: '{cell_value}' (non numerico)")
                        
            print(f"✅ Somma calcolata: {col_sum}")
            print(f"📊 Valori validi: {len(valid_values)}")
            if len(valid_values) <= 5:
                for val in valid_values:
                    print(f"   - {val}")
            else:
                print(f"   - Prime 3: {valid_values[:3]}")
                print(f"   - Ultime 2: {valid_values[-2:]}")
                    
            if invalid_values:
                print(f"⚠️  Valori non numerici: {len(invalid_values)}")
                for val in invalid_values[:3]:  # Mostra solo i primi 3
                    print(f"   - {val}")
                    
        # Trova la riga dei totali attuale
        print("\n🎯 RIGA TOTALI ATTUALE:")
        print("-" * 30)
        
        totals_row = None
        totals_row_idx = None
        
        for row_idx, row in enumerate(values):
            if row and row[0] == "Totali":
                totals_row = row
                totals_row_idx = row_idx
                break
                
        if totals_row:
            print(f"📍 Riga totali trovata alla posizione {totals_row_idx + 1}")
            print(f"📋 Contenuto: {totals_row}")
            
            # Confronta con calcolo corretto
            print("\n🔍 CONFRONTO CALCOLO CORRETTO:")
            print("-" * 35)
            
            for col_idx in range(2, min(len(header), len(totals_row))):
                col_name = header[col_idx] if col_idx < len(header) else f"Col_{col_idx}"
                
                # Calcola somma corretta
                correct_sum = 0
                for row_idx in range(1, len(values)):
                    row = values[row_idx]
                    if row and row[0] == "Totali":
                        continue
                    if col_idx < len(row) and row[col_idx]:
                        try:
                            correct_sum += int(row[col_idx])
                        except (ValueError, TypeError):
                            pass
                            
                current_total = totals_row[col_idx] if col_idx < len(totals_row) else ""
                
                if str(correct_sum) == str(current_total):
                    print(f"✅ {col_name}: {current_total} (corretto)")
                else:
                    print(f"❌ {col_name}: attuale='{current_total}', corretto={correct_sum}")
                    
        else:
            print("⚠️  Nessuna riga totali trovata!")
            
        print("\n" + "=" * 50)
        print("🔍 Debug totali completato")
        
        return True
        
    except Exception as e:
        logger.error(f"Errore nel debug totali: {e}")
        traceback.print_exc()
        return False

def test_credentials():
    """Test delle credenziali Google Sheets"""
    try:
        logger.info("🔍 TEST CREDENZIALI GOOGLE SHEETS")
        logger.info("=" * 50)
        
        # Ottieni credenziali
        credentials_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
        if not credentials_json:
            logger.error("❌ Credenziali non trovate nelle variabili d'ambiente")
            return False
        
        # Esegui test
        tester = CredentialsTest()
        success = tester.test_credentials(credentials_json)
        
        if success:
            logger.info("✅ Test credenziali completato con successo!")
        else:
            logger.error("❌ Test credenziali fallito!")
            
        return success
        
    except Exception as e:
        logger.error(f"Errore nel test credenziali: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Controlla gli argomenti della riga di comando
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "test":
            test_scraping()
        elif command == "performance":
            test_performance()
        elif command == "test-sheets":
            test_sheets()
        elif command == "aggiorna-statico":
            aggiorna_sheet_con_dati_statici()
        elif command == "aggiorna-mensile-statico":
            aggiorna_tab_mensile_statico()
        elif command == "formatta-mensile":
            formatta_tab_mensile()
        elif command == "debug-scraping":
            debug_scraping_issue()
        elif command == "debug-totali":
            debug_totals()
        elif command == "help":
            print("Comandi disponibili:")
            print("  python main.py              - Esegue il monitoraggio completo")
            print("  python main.py test         - Testa solo lo scraping")
            print("  python main.py performance  - Test dettagliato delle performance")
            print("  python main.py test-sheets  - Testa solo Google Sheets")
            print("  python main.py aggiorna-statico - Aggiorna sheet solo con dati statici")
            print("  python main.py aggiorna-mensile-statico - Aggiorna tab mensile con dati statici")
            print("  python main.py formatta-mensile - Applica solo la formattazione alla tab mensile")
            print("  python main.py debug-scraping - Debugga il problema dei dati identici")
            print("  python main.py debug-totali - Debugga i calcoli dei totali nelle Google Sheets")
            print("  python main.py help         - Mostra questo aiuto")
        else:
            print(f"Comando sconosciuto: {command}")
            print("Usa 'python main.py help' per vedere i comandi disponibili")
    else:
        # Esegui il monitoraggio completo
        main() 