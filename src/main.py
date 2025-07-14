"""
Vestiaire Monitor - Main Script
Script principale per l'automazione del monitoraggio Vestiaire
"""

import os
import sys
import logging
import json
from datetime import datetime
from typing import Dict, List, Union
import time # Aggiunto per la funzione debug_scraping_issue

# Aggiungi il percorso src al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import VestiaireScraper
from sheets_updater import GoogleSheetsUpdater

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

def main():
    """Funzione principale del monitoraggio Vestiaire"""
    start_time = datetime.now()
    logger.info("=== INIZIO MONITORAGGIO VESTIAIRE ===")
    
    try:
        # 1. Carica le credenziali
        credentials = load_credentials()
        
        # 2. Esegui lo scraping
        logger.info("Avvio scraping dei profili Vestiaire...")
        scraper = VestiaireScraper()
        scraped_data = scraper.scrape_all_profiles()
        
        if not scraped_data:
            logger.error("Nessun dato estratto dallo scraping")
            return False
        
        # 2.1 VERIFICA DATI SCRAPATI
        logger.info("=== VERIFICA DATI SCRAPATI ===")
        total_articles_scraped = 0
        total_sales_scraped = 0
        profiles_with_data = 0
        
        for profile_data in scraped_data:
            articles = profile_data.get('articles', 0)
            sales = profile_data.get('sales', 0)
            total_articles_scraped += articles
            total_sales_scraped += sales
            
            if articles > 0 or sales > 0:
                profiles_with_data += 1
            
            # Log dettagliato per ogni profilo
            error = profile_data.get('error', '')
            error_msg = f" [ERRORE: {error}]" if error else ""
            logger.info(f"  📊 {profile_data['name']}: {articles} articoli, {sales} vendite{error_msg}")
        
        logger.info(f"📈 TOTALI SCRAPATI: {total_articles_scraped} articoli, {total_sales_scraped} vendite")
        logger.info(f"📋 Profili con dati: {profiles_with_data}/{len(scraped_data)}")
        
        # 2.2 CONTROLLO QUALITÀ DATI
        if total_articles_scraped == 0 and total_sales_scraped == 0:
            logger.error("🚨 ATTENZIONE: Tutti i profili hanno 0 articoli e 0 vendite - possibile fallimento scraping!")
        elif profiles_with_data < len(scraped_data) * 0.5:  # Meno del 50% dei profili ha dati
            logger.warning(f"⚠️  ATTENZIONE: Solo {profiles_with_data} profili su {len(scraped_data)} hanno dati")
        
        # 2.3 CONFRONTO CON DATI NOTI (se sembrano dati statici)
        known_static_totals = {"articles": 16449, "sales": 24950}  # Totali dei dati statici noti
        if (total_articles_scraped == known_static_totals["articles"] and 
            total_sales_scraped == known_static_totals["sales"]):
            logger.warning("⚠️  SOSPETTO: I dati scrapati corrispondono esattamente ai dati statici noti!")
        
        # 3. Calcola i totali
        totals = scraper.calculate_totals(scraped_data)
        logger.info(f"Totale articoli: {totals['total_articles']}")
        logger.info(f"Totale vendite: {totals['total_sales']}")
        
        # 4. Aggiorna Google Sheets se le credenziali sono disponibili
        if credentials:
            sheets_start_time = datetime.now()
            logger.info("Aggiornamento Google Sheets...")
            
            # Se le credenziali sono un dict, convertilo in stringa JSON
            import json as _json
            if isinstance(credentials, dict):
                credentials_json = _json.dumps(credentials)
            else:
                credentials_json = credentials
            sheets_updater = GoogleSheetsUpdater(credentials_json)
            
            # Aggiorna il foglio principale
            success = sheets_updater.update_sheet(scraped_data, sheet_name="riepilogo")
            if success:
                logger.info("Google Sheets aggiornato con successo")
            else:
                logger.error("Errore nell'aggiornamento di Google Sheets")
            
            # Aggiorna la tab mensile con logging dettagliato
            today = datetime.now().date()
            logger.info(f"📅 Aggiornamento tab mensile per: {today.year}-{today.month:02d}-{today.day:02d}")
            logger.info(f"📅 Colonna calcolata: giorno {today.day} = colonna base {2 + (today.day-1)*4}")
            
            monthly_success = sheets_updater.update_monthly_sheet(scraped_data, today.year, today.month, today.day)
            if monthly_success:
                logger.info("Tab mensile aggiornata con successo")
            else:
                logger.error("Errore nell'aggiornamento della tab mensile")
            
            # Crea il riepilogo
            sheets_updater.create_summary_sheet(scraped_data)
            
            sheets_end_time = datetime.now()
            sheets_duration = sheets_end_time - sheets_start_time
            logger.info(f"⏱️ Aggiornamento Google Sheets completato in {sheets_duration.total_seconds():.2f} secondi")
        else:
            logger.info("Saltando l'aggiornamento di Google Sheets (nessuna credenziale)")
        
        # 5. Log dei risultati
        logger.info("=== RISULTATI SCRAPING ===")
        for profile_data in scraped_data:
            logger.info(f"{profile_data['name']}: {profile_data['articles']} articoli, {profile_data['sales']} vendite")
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"🏁 Monitoraggio completato in {duration.total_seconds():.2f} secondi")
        
        # Log statistiche performance se disponibili
        performance_stats = scraper.get_performance_stats()
        if performance_stats.get("total_scraping_time"):
            logger.info(f"📊 Statistiche scraping: {performance_stats['total_scraping_time']:.2f}s totali, {performance_stats['average_profile_time']:.2f}s medi per profilo")
        
        # 6. RIEPILOGO FINALE PER DEBUG
        logger.info("=== RIEPILOGO DEBUG ===")
        logger.info(f"🕐 Timestamp esecuzione: {datetime.now().isoformat()}")
        logger.info(f"📊 Dati processati: {len(scraped_data)} profili")
        logger.info(f"📈 Totali: {total_articles_scraped} articoli, {total_sales_scraped} vendite")
        logger.info(f"📅 Giorno aggiornato nel foglio: {today.day}")
        logger.info(f"🔄 Aggiornamento sheets: {'Successo' if monthly_success else 'Fallito'}")
        
        return True
        
    except Exception as e:
        logger.error(f"Errore generale nel monitoraggio: {e}")
        logger.error(f"Traceback completo:", exc_info=True)
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
            print("  python main.py help         - Mostra questo aiuto")
        else:
            print(f"Comando sconosciuto: {command}")
            print("Usa 'python main.py help' per vedere i comandi disponibili")
    else:
        # Esegui il monitoraggio completo
        main() 