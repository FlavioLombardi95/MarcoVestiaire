"""
Google Sheets Updater
Modulo per aggiornare automaticamente il Google Sheet con i dati Vestiaire
"""

import os
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleSheetsUpdater:
    """Classe per aggiornare Google Sheets con i dati Vestiaire"""
    
    def __init__(self, credentials_json: str = None):
        self.spreadsheet_id = "1sWmvdbEgzLCyaNk5XRDHOFTA5KY1RGeMBIqouXvPJ34"
        self.service = None
        
        if credentials_json:
            self.setup_service(credentials_json)
    
    def setup_service(self, credentials_json: str):
        """Configura il servizio Google Sheets API"""
        try:
            # Parse delle credenziali JSON
            if isinstance(credentials_json, str):
                credentials_dict = json.loads(credentials_json)
            else:
                credentials_dict = credentials_json
            
            # Scope per Google Sheets
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            
            # Crea le credenziali
            credentials = Credentials.from_service_account_info(
                credentials_dict, scopes=scopes
            )
            
            # Crea il servizio
            self.service = build('sheets', 'v4', credentials=credentials)
            logger.info("Servizio Google Sheets configurato con successo")
            
        except Exception as e:
            logger.error(f"Errore nella configurazione del servizio Google Sheets: {e}")
            raise
    
    def get_last_row_data(self, sheet_name: str = "Foglio1") -> Dict:
        """Recupera i dati dell'ultima riga per calcolare le differenze"""
        try:
            # Trova l'ultima riga con dati
            range_name = f"{sheet_name}!A:Z"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return {}
            
            # Cerca l'ultima riga con dati completi
            last_row = None
            for i in range(len(values) - 1, -1, -1):
                row = values[i]
                if len(row) >= 3 and any(cell.strip() for cell in row[:3]):
                    last_row = row
                    break
            
            if not last_row:
                return {}
            
            # Estrai i dati dell'ultima riga
            last_data = {}
            for i, cell in enumerate(last_row):
                if cell.strip():
                    last_data[f"col_{i}"] = cell.strip()
            
            return last_data
            
        except Exception as e:
            logger.error(f"Errore nel recupero dell'ultima riga: {e}")
            return {}
    
    def prepare_data_for_sheet(self, scraped_data: List[Dict], last_data: Dict = None) -> List[List[Any]]:
        """Prepara i dati per l'inserimento nel foglio"""
        today = datetime.now().strftime("%d %B")
        
        # Prepara l'header se necessario
        header = [
            "Profilo", "URL", "Articoli", "Vendite", "Data"
        ]
        
        # Prepara i dati delle righe
        rows = []
        for profile_data in scraped_data:
            row = [
                profile_data.get('name', ''),
                profile_data.get('url', ''),
                profile_data.get('articles', 0),
                profile_data.get('sales', 0),
                today
            ]
            rows.append(row)
        
        # Aggiungi riga dei totali
        total_articles = sum(p.get('articles', 0) for p in scraped_data)
        total_sales = sum(p.get('sales', 0) for p in scraped_data)
        
        totals_row = [
            "TOTALI", "", total_articles, total_sales, today
        ]
        rows.append(totals_row)
        
        return [header] + rows
    
    def clear_sheet(self, sheet_name: str = "riepilogo"):
        """Cancella tutti i dati dal foglio specificato"""
        try:
            if not self.service:
                raise Exception("Servizio Google Sheets non configurato")
            range_name = f"{sheet_name}!A:Z"
            body = {"values": []}
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                body={}
            ).execute()
            logger.info(f"Cancellati tutti i dati dal foglio '{sheet_name}'")
            return True
        except Exception as e:
            logger.error(f"Errore nella cancellazione del foglio: {e}")
            return False

    def update_sheet(self, scraped_data: List[Dict], sheet_name: str = "riepilogo"):
        """Aggiorna il foglio Google Sheets con i nuovi dati, cancellando prima tutto"""
        try:
            if not self.service:
                raise Exception("Servizio Google Sheets non configurato")
            # Cancella tutto prima di scrivere
            self.clear_sheet(sheet_name)
            # Prepara i dati
            data_to_insert = self.prepare_data_for_sheet(scraped_data)
            # Scrivi i nuovi dati dalla prima riga
            range_to_update = f"{sheet_name}!A1"
            body = {
                'values': data_to_insert
            }
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_to_update,
                valueInputOption='RAW',
                body=body
            ).execute()
            logger.info(f"Aggiornamento completato: {result.get('updatedCells')} celle aggiornate")
            # Scrivi il timestamp in G1
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!G1",
                valueInputOption='RAW',
                body={'values': [[timestamp]]}
            ).execute()
            logger.info(f"Timestamp aggiornamento scritto in {sheet_name}!G1: {timestamp}")
            return True
        except HttpError as e:
            logger.error(f"Errore HTTP nell'aggiornamento del foglio: {e}")
            return False
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento del foglio: {e}")
            return False
    
    def create_summary_sheet(self, scraped_data: List[Dict]):
        """Crea un foglio di riepilogo con i dati storici"""
        try:
            if not self.service:
                raise Exception("Servizio Google Sheets non configurato")
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Prepara i dati per il riepilogo
            summary_data = []
            for profile_data in scraped_data:
                summary_row = [
                    today,
                    profile_data.get('name', ''),
                    profile_data.get('articles', 0),
                    profile_data.get('sales', 0),
                    profile_data.get('timestamp', '')
                ]
                summary_data.append(summary_row)
            
            # Inserisci nel foglio "riepilogo"
            range_name = "riepilogo!A:E"
            
            body = {
                'values': summary_data
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"Riepilogo aggiornato: {result.get('updatedCells')} celle aggiornate")
            return True
            
        except Exception as e:
            logger.error(f"Errore nella creazione del riepilogo: {e}")
            return False
    
    def format_sheet(self, sheet_name: str = "Foglio1"):
        """Applica formattazione al foglio"""
        try:
            if not self.service:
                raise Exception("Servizio Google Sheets non configurato")
            
            # Formattazione per l'header
            header_format = {
                "backgroundColor": {
                    "red": 0.2,
                    "green": 0.6,
                    "blue": 0.8
                },
                "textFormat": {
                    "bold": True,
                    "foregroundColor": {
                        "red": 1,
                        "green": 1,
                        "blue": 1
                    }
                }
            }
            
            # Applica formattazione all'header
            requests = [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": 0,  # Assumiamo che sia il primo foglio
                            "startRowIndex": 0,
                            "endRowIndex": 1
                        },
                        "cell": {
                            "userEnteredFormat": header_format
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat)"
                    }
                }
            ]
            
            body = {
                "requests": requests
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            logger.info("Formattazione applicata con successo")
            return True
            
        except Exception as e:
            logger.error(f"Errore nell'applicazione della formattazione: {e}")
            return False

def main():
    """Funzione principale per testare l'updater"""
    # Test con dati di esempio
    test_data = [
        {
            "name": "Rediscover",
            "url": "https://it.vestiairecollective.com/profile/2039815/",
            "articles": 573,
            "sales": 7198,
            "timestamp": "2024-01-15 10:00:00"
        },
        {
            "name": "Volodymyr", 
            "url": "https://it.vestiairecollective.com/profile/5924329/",
            "articles": 2315,
            "sales": 5558,
            "timestamp": "2024-01-15 10:00:00"
        }
    ]
    
    print("=== TEST SHEETS UPDATER ===")
    print("Dati di test preparati")
    print("Nota: Per testare completamente, configurare le credenziali Google Sheets")

if __name__ == "__main__":
    main() 