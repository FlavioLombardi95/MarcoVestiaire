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
import calendar

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
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            logger.info(f"Aggiornamento completato: {result.get('updatedCells')} celle aggiornate")
            # Scrivi il timestamp in G1
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!G1",
                valueInputOption='USER_ENTERED',
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
                valueInputOption='USER_ENTERED',
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

    def format_monthly_sheet(self, month_name: str, year: int):
        """Formatta la tab mensile: merge celle, header, colori alternati, larghezza colonne."""
        try:
            days = calendar.monthrange(year, list(calendar.month_name).index(month_name.capitalize()))[1]
            # Merge celle riga 1 per ogni giorno
            requests = []
            sheet_id = self._get_sheet_id(month_name)
            logger.info(f"[FORMAT] sheet_id trovato per '{month_name}': {sheet_id}")
            # Calcola il numero di righe dati (senza la riga Totali)
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{month_name}!A:ZZ"
            ).execute()
            values = result.get('values', [])
            num_data_rows = len(values) - 1 if values and values[-1][0] == "Totali" else len(values)
            end_row = num_data_rows  # escludi la riga Totali
            logger.info(f"[FORMAT] Colori alternati fino a riga: {end_row}")
            start_col = 2
            for d in range(1, days+1):
                end_col = start_col + 3
                requests.append({
                    "mergeCells": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": start_col,
                            "endColumnIndex": end_col+1
                        },
                        "mergeType": "MERGE_ALL"
                    }
                })
                start_col = end_col+1
            # Colori alternati (bianco/blu chiaro ben visibile) SOLO sulle righe dati
            start_col = 2
            for d in range(1, days+1):
                end_col = start_col + 3
                color = {"red": 0.89, "green": 0.94, "blue": 0.99} if d % 2 == 0 else {"red": 1, "green": 1, "blue": 1}
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": end_row,  # solo fino ai dati
                            "startColumnIndex": start_col,
                            "endColumnIndex": end_col+1
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": color
                            }
                        },
                        "fields": "userEnteredFormat.backgroundColor"
                    }
                })
                start_col = end_col+1
            # Larghezza colonne
            for c in range(2, 2+days*4):
                requests.append({
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": c,
                            "endIndex": c+1
                        },
                        "properties": {"pixelSize": 60},
                        "fields": "pixelSize"
                    }
                })
            logger.info(f"[FORMAT] Numero richieste batch da inviare: {len(requests)}")
            # Applica richieste
            resp = self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={"requests": requests}
            ).execute()
            logger.info(f"[FORMAT] Risposta batchUpdate: {resp}")
            logger.info(f"Formattazione tab {month_name} completata")
        except Exception as e:
            logger.error(f"Errore nella formattazione tab mensile: {e}")

    def _get_sheet_id(self, month_name: str):
        spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
        for s in spreadsheet['sheets']:
            if s['properties']['title'] == month_name:
                return s['properties']['sheetId']
        raise Exception(f"Sheet {month_name} non trovato")

    def create_monthly_tab(self, month_name: str, year: int):
        """Crea la tab del mese con tutte le intestazioni se non esiste."""
        try:
            # Ottieni lista delle tab
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheet_names = [s['properties']['title'] for s in spreadsheet['sheets']]
            if month_name not in sheet_names:
                # Crea la tab
                requests = [{
                    "addSheet": {
                        "properties": {
                            "title": month_name
                        }
                    }
                }]
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={"requests": requests}
                ).execute()
                logger.info(f"Tab '{month_name}' creata")
                # Prepara intestazioni
                days = calendar.monthrange(year, list(calendar.month_name).index(month_name.capitalize()))[1]
                # Riga 1: date (merge da formattazione)
                header1 = ["Profilo", "URL"]
                for d in range(1, days+1):
                    header1 += [f"{d} {month_name}", "", "", ""]
                # Riga 2: etichette
                header2 = ["", ""]
                for d in range(1, days+1):
                    header2 += ["articoli", "vendite", "diff stock", "diff vendite"]
                # Scrivi intestazioni
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{month_name}!A1",
                    valueInputOption='USER_ENTERED',
                    body={'values': [header1, header2]}
                ).execute()
                logger.info(f"Intestazioni scritte su '{month_name}'")
                # Applica formattazione
                self.format_monthly_sheet(month_name, year)
        except Exception as e:
            logger.error(f"Errore nella creazione tab mensile: {e}")

    def update_monthly_sheet(self, scraped_data: list, year: int, month: int, day: int):
        """Aggiorna la tab mensile con i dati del giorno, calcolando le differenze."""
        import copy
        month_name = calendar.month_name[month].lower()
        self.create_monthly_tab(month_name, year)
        # Leggi dati attuali
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=f"{month_name}!A:ZZ"
        ).execute()
        values = result.get('values', [])
        if not values:
            logger.error(f"Tab {month_name} vuota!")
            return False
        header = values[0]
        # Mappa profilo->riga
        profilo_to_row = {row[0]: i for i, row in enumerate(values[1:], start=2) if row and row[0]}
        # Calcola colonne da aggiornare
        base_col = 2 + (day-1)*4
        articoli_col = base_col
        vendite_col = base_col+1
        diff_stock_col = base_col+2
        diff_vendite_col = base_col+3
        # Prepara update
        updates = []
        for profilo in scraped_data:
            name = profilo['name']
            url = profilo['url']
            articoli = profilo['articles']
            vendite = profilo['sales']
            # Trova riga
            if name in profilo_to_row:
                row_idx = profilo_to_row[name]
                row = copy.deepcopy(values[row_idx-1]) if row_idx-1 < len(values) else [name, url]
            else:
                # Nuovo profilo
                row = [name, url] + ["" for _ in range(len(header)-2)]
                values.append(row)
                row_idx = len(values)
                # Aggiorna mapping
                profilo_to_row[name] = row_idx
            # Calcola differenze
            prev_articoli = None
            prev_vendite = None
            if articoli_col-4 < len(row):
                try:
                    if row[articoli_col-4]:
                        clean_val = str(row[articoli_col-4]).replace("'", "").replace(" ", "").strip()
                        prev_articoli = int(clean_val) if clean_val else None
                    else:
                        prev_articoli = None
                except (ValueError, TypeError):
                    prev_articoli = None
                try:
                    if row[vendite_col-4]:
                        clean_val = str(row[vendite_col-4]).replace("'", "").replace(" ", "").strip()
                        prev_vendite = int(clean_val) if clean_val else None
                    else:
                        prev_vendite = None
                except (ValueError, TypeError):
                    prev_vendite = None
            diff_stock = articoli - prev_articoli if prev_articoli is not None else ""
            diff_vendite = vendite - prev_vendite if prev_vendite is not None else ""
            # Allunga la riga se serve
            while len(row) < diff_vendite_col+1:
                row.append("")
            row[articoli_col] = articoli  # Mantieni come numero
            row[vendite_col] = vendite    # Mantieni come numero
            row[diff_stock_col] = diff_stock if diff_stock != "" else ""
            row[diff_vendite_col] = diff_vendite if diff_vendite != "" else ""
            # Aggiorna la riga in values
            values[row_idx-1] = row
        # Calcola e aggiungi la riga dei totali
        num_cols = len(header)
        num_rows = len(values)
        totali_row = ["Totali", ""]
        for c in range(2, num_cols):
            col_sum = 0
            for r in range(1, num_rows):
                try:
                    if c < len(values[r]) and values[r][c]:
                        # Pulisce il valore da apostrofi e spazi
                        clean_val = str(values[r][c]).replace("'", "").replace(" ", "").strip()
                        val = int(clean_val) if clean_val else 0
                    else:
                        val = 0
                except (ValueError, TypeError):
                    val = 0
                col_sum += val
            totali_row.append(col_sum)  # Sempre mostra il numero, anche se è 0
        # Rimuovi eventuale riga Totali precedente
        values = [row for row in values if not (row and row[0] == "Totali")]
        values.append(totali_row)
        # Scrivi tutte le righe aggiornate
        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f"{month_name}!A1",
            valueInputOption='USER_ENTERED',
            body={'values': values}
        ).execute()
        # Applica sfondo grigio chiaro alla riga Totali
        try:
            sheet_id = self._get_sheet_id(month_name)
            requests = [{
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": len(values)-1,
                        "endRowIndex": len(values),
                        "startColumnIndex": 0,
                        "endColumnIndex": num_cols
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
                        }
                    },
                    "fields": "userEnteredFormat.backgroundColor"
                }
            }]
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={"requests": requests}
            ).execute()
        except Exception as e:
            logger.error(f"Errore nella formattazione della riga Totali: {e}")
        logger.info(f"Tab {month_name} aggiornata con i dati del giorno {day} e riga Totali")
        self.format_monthly_sheet(month_name, year)
        return True

    def format_only_monthly_sheet(self, month_name: str, year: int):
        """Applica solo la formattazione a una tab mensile già esistente, senza toccare i dati."""
        self.format_monthly_sheet(month_name, year)

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