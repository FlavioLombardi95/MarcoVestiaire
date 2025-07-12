"""
Vestiaire Monitor - Main Script
Script principale per l'automazione del monitoraggio Vestiaire
"""

import os
import sys
import logging
import json
from datetime import datetime
from typing import Dict, List

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
    """Carica le credenziali Google Sheets da variabile d'ambiente"""
    try:
        # Prova a caricare da variabile d'ambiente
        credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
        if credentials_json:
            return json.loads(credentials_json)
        
        # Prova a caricare da file
        credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE')
        if credentials_file and os.path.exists(credentials_file):
            with open(credentials_file, 'r') as f:
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
            sheets_updater = GoogleSheetsUpdater(credentials)
            
            # Aggiorna il foglio principale
            success = sheets_updater.update_sheet(scraped_data)
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
        
        sheets_updater = GoogleSheetsUpdater(credentials)
        success = sheets_updater.update_sheet(test_data)
        
        if success:
            logger.info("Test Google Sheets completato con successo")
        else:
            logger.error("Test Google Sheets fallito")
        
        return success
        
    except Exception as e:
        logger.error(f"Errore nel test Google Sheets: {e}")
        return False

if __name__ == "__main__":
    # Controlla gli argomenti della riga di comando
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            test_scraping()
        elif command == "test-sheets":
            test_sheets()
        elif command == "help":
            print("Comandi disponibili:")
            print("  python main.py          - Esegue il monitoraggio completo")
            print("  python main.py test     - Testa solo lo scraping")
            print("  python main.py test-sheets - Testa solo Google Sheets")
            print("  python main.py help     - Mostra questo aiuto")
        else:
            print(f"Comando sconosciuto: {command}")
            print("Usa 'python main.py help' per vedere i comandi disponibili")
    else:
        # Esegui il monitoraggio completo
        main() 