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
        
        # 3. Calcola i totali
        totals = scraper.calculate_totals(scraped_data)
        logger.info(f"Totale articoli: {totals['total_articles']}")
        logger.info(f"Totale vendite: {totals['total_sales']}")
        
        # 4. Aggiorna Google Sheets se le credenziali sono disponibili
        if credentials:
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
            
            # Crea il riepilogo
            sheets_updater.create_summary_sheet(scraped_data)
        else:
            logger.info("Saltando l'aggiornamento di Google Sheets (nessuna credenziale)")
        
        # 5. Log dei risultati
        logger.info("=== RISULTATI SCRAPING ===")
        for profile_data in scraped_data:
            logger.info(f"{profile_data['name']}: {profile_data['articles']} articoli, {profile_data['sales']} vendite")
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Monitoraggio completato in {duration.total_seconds():.2f} secondi")
        
        return True
        
    except Exception as e:
        logger.error(f"Errore generale nel monitoraggio: {e}")
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

def test_sheets():
    """Funzione di test per Google Sheets"""
    logger.info("=== TEST GOOGLE SHEETS ===")
    
    try:
        credentials = load_credentials()
        if not credentials:
            logger.warning("Nessuna credenziale disponibile per il test")
            return False
        # Se le credenziali sono un dict, convertilo in stringa JSON
        import json as _json
        if isinstance(credentials, dict):
            credentials_json = _json.dumps(credentials)
        else:
            credentials_json = credentials
        # Dati di test
        test_data = [
            {
                "name": "Test Profile",
                "url": "https://test.com",
                "articles": 100,
                "sales": 50,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        ]
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

if __name__ == "__main__":
    # Controlla gli argomenti della riga di comando
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "test":
            test_scraping()
        elif command == "test-sheets":
            test_sheets()
        elif command == "aggiorna-statico":
            aggiorna_sheet_con_dati_statici()
        elif command == "aggiorna-mensile-statico":
            aggiorna_tab_mensile_statico()
        elif command == "formatta-mensile":
            formatta_tab_mensile()
        elif command == "help":
            print("Comandi disponibili:")
            print("  python main.py          - Esegue il monitoraggio completo")
            print("  python main.py test     - Testa solo lo scraping")
            print("  python main.py test-sheets - Testa solo Google Sheets")
            print("  python main.py aggiorna-statico - Aggiorna sheet solo con dati statici, cancellando tutto prima")
            print("  python main.py aggiorna-mensile-statico - Aggiorna la tab mensile con dati statici e logica nuova")
            print("  python main.py formatta-mensile - Applica solo la formattazione alla tab del mese corrente")
            print("  python main.py help     - Mostra questo aiuto")
        else:
            print(f"Comando sconosciuto: {command}")
            print("Usa 'python main.py help' per vedere i comandi disponibili")
    else:
        # Esegui il monitoraggio completo
        main() 