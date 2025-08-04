"""
Google Sheets Updater
Modulo per aggiornare automaticamente il Google Sheet con i dati Vestiaire
"""

import os
import logging
import time
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
            start_col = 3  # +3 perché ora abbiamo Profilo, Diff Vendite, URL
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
            start_col = 3  # +3 perché ora abbiamo Profilo, Diff Vendite, URL
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
            for c in range(3, 3+days*4):  # +3 perché ora abbiamo Profilo, Diff Vendite, URL
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
                header1 = ["Profilo", f"Diff Vendite {month_name.capitalize()}", "URL"]
                for d in range(1, days+1):
                    header1 += [f"{d} {month_name}", "", "", ""]
                # Riga 2: etichette
                header2 = ["", "", ""]
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

    def update_previous_days_diffs(self, month_name: str, year: int, month: int, day: int):
        """Aggiorna i calcoli delle differenze per tutti i giorni precedenti del mese."""
        try:
            logger.info(f"Aggiornamento differenze per i giorni precedenti in {month_name}")
            
            # Leggi dati attuali
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{month_name}!A:ZZ"
            ).execute()
            values = result.get('values', [])
            
            if not values or len(values) < 3:
                logger.info(f"Tab {month_name} non ha dati sufficienti per aggiornare differenze")
                return
            
            # Per ogni giorno dal 2 in poi, calcola le differenze
            for current_day in range(2, day + 1):
                logger.info(f"Calcolo differenze per il giorno {current_day}")
                
                # Calcola colonne per il giorno corrente
                base_col = 3 + (current_day-1)*4
                articoli_col = base_col
                vendite_col = base_col+1
                diff_stock_col = base_col+2
                diff_vendite_col = base_col+3
                
                # Calcola colonne per il giorno precedente
                prev_articoli_col = 3 + (current_day-2)*4
                prev_vendite_col = 4 + (current_day-2)*4
                
                # Per ogni riga profilo (escludi header e totali)
                for row_idx in range(2, len(values)):
                    if values[row_idx] and values[row_idx][0] and values[row_idx][0] != "Totali":
                        row = values[row_idx]
                        
                        # Allunga la riga se necessario
                        while len(row) < diff_vendite_col + 1:
                            row.append("")
                        
                        # Leggi dati del giorno corrente
                        current_articoli = None
                        current_vendite = None
                        
                        if articoli_col < len(row) and row[articoli_col]:
                            try:
                                clean_val = str(row[articoli_col]).replace("'", "").replace(" ", "").strip()
                                current_articoli = int(clean_val) if clean_val else None
                            except (ValueError, TypeError):
                                current_articoli = None
                        
                        if vendite_col < len(row) and row[vendite_col]:
                            try:
                                clean_val = str(row[vendite_col]).replace("'", "").replace(" ", "").strip()
                                current_vendite = int(clean_val) if clean_val else None
                            except (ValueError, TypeError):
                                current_vendite = None
                        
                        # Leggi dati del giorno precedente
                        prev_articoli = None
                        prev_vendite = None
                        
                        if prev_articoli_col < len(row) and row[prev_articoli_col]:
                            try:
                                clean_val = str(row[prev_articoli_col]).replace("'", "").replace(" ", "").strip()
                                prev_articoli = int(clean_val) if clean_val else None
                            except (ValueError, TypeError):
                                prev_articoli = None
                        
                        if prev_vendite_col < len(row) and row[prev_vendite_col]:
                            try:
                                clean_val = str(row[prev_vendite_col]).replace("'", "").replace(" ", "").strip()
                                prev_vendite = int(clean_val) if clean_val else None
                            except (ValueError, TypeError):
                                prev_vendite = None
                        
                        # Calcola differenze solo se abbiamo entrambi i valori
                        if current_articoli is not None and prev_articoli is not None:
                            diff_stock = current_articoli - prev_articoli
                            row[diff_stock_col] = diff_stock
                            logger.info(f"  {row[0]} giorno {current_day}: diff_stock = {current_articoli} - {prev_articoli} = {diff_stock}")
                        
                        if current_vendite is not None and prev_vendite is not None:
                            diff_vendite = current_vendite - prev_vendite
                            row[diff_vendite_col] = diff_vendite
                            logger.info(f"  {row[0]} giorno {current_day}: diff_vendite = {current_vendite} - {prev_vendite} = {diff_vendite}")
            
            # Scrivi i dati aggiornati
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{month_name}!A1",
                valueInputOption='USER_ENTERED',
                body={'values': values}
            ).execute()
            
            logger.info(f"Differenze aggiornate per i giorni precedenti in {month_name}")
            
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento delle differenze precedenti: {e}")

    def get_previous_month_last_day_data(self, year: int, month: int) -> Dict[str, Dict]:
        """Recupera i dati dell'ultimo giorno del mese precedente per calcolare le differenze del primo giorno."""
        try:
            # Calcola il mese precedente
            if month == 1:
                prev_month = 12
                prev_year = year - 1
            else:
                prev_month = month - 1
                prev_year = year
            
            prev_month_name = calendar.month_name[prev_month].lower()
            logger.info(f"Recupero dati del mese precedente: {prev_month_name} {prev_year}")
            
            # Ottieni l'ultimo giorno del mese precedente
            last_day = calendar.monthrange(prev_year, prev_month)[1]
            
            logger.info(f"Recupero dati del {last_day} {prev_month_name} {prev_year}")
            
            # Leggi i dati dell'ultimo giorno del mese precedente
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{prev_month_name}!A:ZZ"
            ).execute()
            values = result.get('values', [])
            
            logger.info(f"Tab {prev_month_name}: trovate {len(values)} righe")
            if len(values) > 0:
                logger.info(f"Prima riga: {values[0]}")
            if len(values) > 1:
                logger.info(f"Seconda riga: {values[1]}")
            
            if not values or len(values) < 3:
                logger.info(f"Tab {prev_month_name} non ha dati sufficienti")
                return {}
            
            # Calcola colonne per l'ultimo giorno del mese precedente
            # Struttura: Profilo, Diff Vendite, URL, [dati giornalieri]
            # I dati giornalieri iniziano dalla colonna D (indice 3)
            base_col = 3 + (last_day-1)*4
            articoli_col = base_col
            vendite_col = base_col+1
            
            # Verifica se le colonne sono ragionevoli
            if base_col > 50:  # Se la colonna è troppo alta, potrebbe essere un errore
                logger.warning(f"Colonna {base_col} per il giorno {last_day} sembra troppo alta!")
                logger.warning("Verificare la struttura della tab {prev_month_name}")
                # Prova a calcolare in modo diverso
                logger.info("Tentativo di calcolo alternativo...")
                # Se il calcolo è sbagliato, prova a cercare le colonne dinamicamente
                return self.find_last_day_data_dynamically(prev_month_name, last_day, values)
            
            logger.info(f"Ultimo giorno {last_day}: colonne calcolate - articoli={articoli_col}, vendite={vendite_col}")
            logger.info(f"Base colonna: {base_col} (giorno {last_day} del mese {prev_month_name})")
            
            # Estrai i dati per ogni profilo
            previous_data = {}
            for row_idx in range(2, len(values)):
                if values[row_idx] and values[row_idx][0] and values[row_idx][0] != "Totali":
                    profile_name = values[row_idx][0]
                    
                    articoli = None
                    vendite = None
                    
                    if articoli_col < len(values[row_idx]) and values[row_idx][articoli_col]:
                        try:
                            clean_val = str(values[row_idx][articoli_col]).replace("'", "").replace(" ", "").strip()
                            articoli = int(clean_val) if clean_val else None
                        except (ValueError, TypeError):
                            articoli = None
                    
                    if vendite_col < len(values[row_idx]) and values[row_idx][vendite_col]:
                        try:
                            clean_val = str(values[row_idx][vendite_col]).replace("'", "").replace(" ", "").strip()
                            vendite = int(clean_val) if clean_val else None
                        except (ValueError, TypeError):
                            vendite = None
                    
                    if articoli is not None or vendite is not None:
                        previous_data[profile_name] = {
                            'articles': articoli,
                            'sales': vendite
                        }
                        logger.info(f"Dati precedenti per {profile_name}: articoli={articoli}, vendite={vendite}")
            
            return previous_data
            
        except Exception as e:
            logger.error(f"Errore nel recupero dati mese precedente: {e}")
            return {}

    def find_last_day_data_dynamically(self, month_name: str, last_day: int, values: list) -> Dict[str, Dict]:
        """Trova i dati dell'ultimo giorno cercando dinamicamente nelle intestazioni."""
        try:
            logger.info(f"Ricerca dinamica dei dati del giorno {last_day} in {month_name}")
            
            if not values or len(values) < 2:
                logger.error("Dati insufficienti per ricerca dinamica")
                return {}
            
            # Cerca nelle intestazioni della riga 1
            header_row = values[0]
            logger.info(f"Header row: {header_row}")
            
            # Cerca la colonna che contiene il giorno
            target_day_header = f"{last_day} {month_name}"
            articoli_col = None
            vendite_col = None
            
            for col_idx, header in enumerate(header_row):
                if header and str(header).strip() == target_day_header:
                    logger.info(f"Trovata intestazione '{target_day_header}' alla colonna {col_idx}")
                    # Le colonne sono: articoli, vendite, diff stock, diff vendite
                    articoli_col = col_idx
                    vendite_col = col_idx + 1
                    break
            
            if articoli_col is None:
                logger.error(f"Intestazione '{target_day_header}' non trovata!")
                logger.info("Intestazioni disponibili:")
                for col_idx, header in enumerate(header_row):
                    if header and str(header).strip():
                        logger.info(f"  Colonna {col_idx}: '{header}'")
                return {}
            
            logger.info(f"Colonne trovate: articoli={articoli_col}, vendite={vendite_col}")
            
            # Estrai i dati per ogni profilo
            previous_data = {}
            for row_idx in range(2, len(values)):
                if values[row_idx] and values[row_idx][0] and values[row_idx][0] != "Totali":
                    profile_name = values[row_idx][0]
                    
                    articoli = None
                    vendite = None
                    
                    if articoli_col < len(values[row_idx]) and values[row_idx][articoli_col]:
                        try:
                            clean_val = str(values[row_idx][articoli_col]).replace("'", "").replace(" ", "").strip()
                            articoli = int(clean_val) if clean_val else None
                        except (ValueError, TypeError):
                            articoli = None
                    
                    if vendite_col < len(values[row_idx]) and values[row_idx][vendite_col]:
                        try:
                            clean_val = str(values[row_idx][vendite_col]).replace("'", "").replace(" ", "").strip()
                            vendite = int(clean_val) if clean_val else None
                        except (ValueError, TypeError):
                            vendite = None
                    
                    if articoli is not None or vendite is not None:
                        previous_data[profile_name] = {
                            'articles': articoli,
                            'sales': vendite
                        }
                        logger.info(f"Dati dinamici per {profile_name}: articoli={articoli}, vendite={vendite}")
            
            return previous_data
            
        except Exception as e:
            logger.error(f"Errore nella ricerca dinamica: {e}")
            return {}

    def recalculate_all_month_diffs(self, month_name: str, year: int, month: int):
        """Ricalcola tutte le differenze per un intero mese."""
        try:
            logger.info(f"Ricalcolo di tutte le differenze per {month_name} {year}")
            
            # Ottieni il numero di giorni nel mese
            days_in_month = calendar.monthrange(year, month)[1]
            
            # Leggi dati attuali
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{month_name}!A:ZZ"
            ).execute()
            values = result.get('values', [])
            
            if not values or len(values) < 3:
                logger.error(f"Tab {month_name} non ha dati sufficienti")
                return False
            
            # Recupera dati del mese precedente per il primo giorno
            previous_month_data = self.get_previous_month_last_day_data(year, month)
            
            # Per ogni giorno del mese, calcola le differenze
            for current_day in range(1, days_in_month + 1):
                logger.info(f"Ricalcolo differenze per il giorno {current_day}")
                
                # Calcola colonne per il giorno corrente
                base_col = 3 + (current_day-1)*4
                articoli_col = base_col
                vendite_col = base_col+1
                diff_stock_col = base_col+2
                diff_vendite_col = base_col+3
                
                # Per ogni riga profilo (escludi header e totali)
                for row_idx in range(2, len(values)):
                    if values[row_idx] and values[row_idx][0] and values[row_idx][0] != "Totali":
                        row = values[row_idx]
                        profile_name = row[0]
                        
                        # Allunga la riga se necessario
                        while len(row) < diff_vendite_col + 1:
                            row.append("")
                        
                        # Leggi dati del giorno corrente
                        current_articoli = None
                        current_vendite = None
                        
                        if articoli_col < len(row) and row[articoli_col]:
                            try:
                                clean_val = str(row[articoli_col]).replace("'", "").replace(" ", "").strip()
                                current_articoli = int(clean_val) if clean_val else None
                            except (ValueError, TypeError):
                                current_articoli = None
                        
                        if vendite_col < len(row) and row[vendite_col]:
                            try:
                                clean_val = str(row[vendite_col]).replace("'", "").replace(" ", "").strip()
                                current_vendite = int(clean_val) if clean_val else None
                            except (ValueError, TypeError):
                                current_vendite = None
                        
                        # Determina dati precedenti
                        prev_articoli = None
                        prev_vendite = None
                        
                        if current_day == 1:  # Primo giorno - usa dati del mese precedente
                            if profile_name in previous_month_data:
                                prev_articoli = previous_month_data[profile_name].get('articles')
                                prev_vendite = previous_month_data[profile_name].get('sales')
                        else:  # Altri giorni - usa dati del giorno precedente
                            prev_articoli_col = 3 + (current_day-2)*4
                            prev_vendite_col = 4 + (current_day-2)*4
                            
                            if prev_articoli_col < len(row) and row[prev_articoli_col]:
                                try:
                                    clean_val = str(row[prev_articoli_col]).replace("'", "").replace(" ", "").strip()
                                    prev_articoli = int(clean_val) if clean_val else None
                                except (ValueError, TypeError):
                                    prev_articoli = None
                            
                            if prev_vendite_col < len(row) and row[prev_vendite_col]:
                                try:
                                    clean_val = str(row[prev_vendite_col]).replace("'", "").replace(" ", "").strip()
                                    prev_vendite = int(clean_val) if clean_val else None
                                except (ValueError, TypeError):
                                    prev_vendite = None
                        
                        # Calcola differenze solo se abbiamo entrambi i valori
                        if current_articoli is not None and prev_articoli is not None:
                            diff_stock = current_articoli - prev_articoli
                            row[diff_stock_col] = diff_stock
                            logger.info(f"  {profile_name} giorno {current_day}: diff_stock = {current_articoli} - {prev_articoli} = {diff_stock}")
                        
                        if current_vendite is not None and prev_vendite is not None:
                            diff_vendite = current_vendite - prev_vendite
                            row[diff_vendite_col] = diff_vendite
                            logger.info(f"  {profile_name} giorno {current_day}: diff_vendite = {current_vendite} - {prev_vendite} = {diff_vendite}")
            
            # Scrivi i dati aggiornati
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{month_name}!A1",
                valueInputOption='USER_ENTERED',
                body={'values': values}
            ).execute()
            
            # Aggiorna i totali mensili delle diff vendite
            self.update_monthly_diff_vendite_totals(month_name, year)
            
            logger.info(f"Ricalcolo completato per {month_name} {year}")
            return True
            
        except Exception as e:
            logger.error(f"Errore nel ricalcolo delle differenze per {month_name}: {e}")
            return False

    def update_monthly_sheet(self, scraped_data: list, year: int, month: int, day: int):
        """Aggiorna la tab mensile con i dati del giorno, calcolando le differenze."""
        import copy
        month_name = calendar.month_name[month].lower()
        self.create_monthly_tab(month_name, year)
        
        # Aggiorna anche i dati dei giorni precedenti se necessario
        if day > 1:
            self.update_previous_days_diffs(month_name, year, month, day)
        
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
        logger.info(f"Header della tab {month_name}: {header}")
        if len(values) > 1:
            logger.info(f"Seconda riga (intestazioni colonne): {values[1]}")
        
        # Mappa profilo->riga
        profilo_to_row = {row[0]: i for i, row in enumerate(values[1:], start=2) if row and row[0]}
        
        # Rimuovi profili che non sono più nella configurazione
        profili_configurati = {profilo['name'] for profilo in scraped_data}
        logger.info(f"Profili configurati: {profili_configurati}")
        
        righe_da_rimuovere = []
        for i, row in enumerate(values[1:], start=1):
            if row and row[0] and row[0] not in profili_configurati and row[0] != "Totali":
                righe_da_rimuovere.append(i)
                logger.info(f"Trovato profilo da rimuovere: {row[0]} (riga {i})")
        
        logger.info(f"Righe da rimuovere: {righe_da_rimuovere}")
        
        # Rimuovi le righe in ordine inverso per non alterare gli indici
        for i in sorted(righe_da_rimuovere, reverse=True):
            if i < len(values):
                profilo_rimosso = values[i][0] if i < len(values) else 'Unknown'
                del values[i]
                logger.info(f"Rimosso profilo obsoleto: {profilo_rimosso}")
        
        # Ricostruisci la mappa profilo->riga dopo la rimozione
        profilo_to_row = {row[0]: i for i, row in enumerate(values[1:], start=2) if row and row[0]}
        
        # Calcola colonne da aggiornare (struttura: Profilo, Diff Vendite, URL, dati giornalieri)
        # I dati giornalieri iniziano dalla colonna D (indice 3)
        # Calcolo dinamico basato sul giorno del mese
        base_col = 3 + (day-1)*4  # 1° giorno = colonna D, 2° giorno = colonna H, ecc.
        articoli_col = base_col
        vendite_col = base_col+1
        diff_stock_col = base_col+2
        diff_vendite_col = base_col+3
        
        logger.info(f"Giorno {day}: colonne calcolate - articoli={articoli_col}, vendite={vendite_col}, diff_stock={diff_stock_col}, diff_vendite={diff_vendite_col}")
        
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
                row = copy.deepcopy(values[row_idx-1]) if row_idx-1 < len(values) else [name, "", url]
            else:
                # Nuovo profilo (con seconda colonna per diff vendite mensile)
                # Struttura: Profilo, Diff Vendite, URL, ...dati giornalieri
                row = [name, "", url] + ["" for _ in range(len(header)-3)]
                values.append(row)
                row_idx = len(values)
                # Aggiorna mapping
                profilo_to_row[name] = row_idx
            
            # Aggiorna sempre l'URL nella colonna C (indice 2)
            if len(row) > 2:
                row[2] = url
            
            # Calcola differenze
            prev_articoli = None
            prev_vendite = None
            
            if day == 1:  # Primo giorno del mese - usa dati del mese precedente
                logger.info(f"Primo giorno del mese {month}, recupero dati del mese precedente")
                previous_month_data = self.get_previous_month_last_day_data(year, month)
                if name in previous_month_data:
                    prev_articoli = previous_month_data[name].get('articles')
                    prev_vendite = previous_month_data[name].get('sales')
                    logger.info(f"  Dati mese precedente per {name}: articoli={prev_articoli}, vendite={prev_vendite}")
                else:
                    logger.info(f"  Nessun dato del mese precedente trovato per {name}")
            
            elif day > 1:  # Giorni successivi - usa dati del giorno precedente
                prev_articoli_col = 3 + (day-2)*4  # Giorno precedente
                prev_vendite_col = 4 + (day-2)*4   # Giorno precedente
                
                if prev_articoli_col < len(row):
                    try:
                        if row[prev_articoli_col]:
                            clean_val = str(row[prev_articoli_col]).replace("'", "").replace(" ", "").strip()
                            prev_articoli = int(clean_val) if clean_val else None
                            logger.info(f"  Dati giorno precedente: articoli={row[prev_articoli_col]} -> {prev_articoli}")
                        else:
                            prev_articoli = None
                            logger.info(f"  Dati giorno precedente: articoli vuoto")
                    except (ValueError, TypeError) as e:
                        prev_articoli = None
                        logger.warning(f"  Errore nel parsing articoli precedenti '{row[prev_articoli_col]}': {e}")
                
                if prev_vendite_col < len(row):
                    try:
                        if row[prev_vendite_col]:
                            clean_val = str(row[prev_vendite_col]).replace("'", "").replace(" ", "").strip()
                            prev_vendite = int(clean_val) if clean_val else None
                            logger.info(f"  Dati giorno precedente: vendite={row[prev_vendite_col]} -> {prev_vendite}")
                        else:
                            prev_vendite = None
                            logger.info(f"  Dati giorno precedente: vendite vuoto")
                    except (ValueError, TypeError) as e:
                        prev_vendite = None
                        logger.warning(f"  Errore nel parsing vendite precedenti '{row[prev_vendite_col]}': {e}")
            
            # Calcolo normale per tutti i casi
            diff_stock = articoli - prev_articoli if prev_articoli is not None else ""
            diff_vendite = vendite - prev_vendite if prev_vendite is not None else ""
            
            # Log per debug
            logger.info(f"Profilo {name}: articoli={articoli}, vendite={vendite}, prev_articoli={prev_articoli}, prev_vendite={prev_vendite}")
            logger.info(f"  Calcoli: diff_stock={diff_stock}, diff_vendite={diff_vendite}")
            logger.info(f"  Colonne: articoli_col={articoli_col}, vendite_col={vendite_col}, diff_stock_col={diff_stock_col}, diff_vendite_col={diff_vendite_col}")
            
            # Allunga la riga se serve
            while len(row) < diff_vendite_col+1:
                row.append("")
            
            row[articoli_col] = articoli  # Mantieni come numero
            row[vendite_col] = vendite    # Mantieni come numero
            row[diff_stock_col] = diff_stock if diff_stock != "" else ""
            row[diff_vendite_col] = diff_vendite if diff_vendite != "" else ""
            
            # Log per verificare che i dati siano stati assegnati correttamente
            logger.info(f"  Dati assegnati: row[{articoli_col}]={row[articoli_col]}, row[{vendite_col}]={row[vendite_col]}")
            logger.info(f"  Diff assegnati: row[{diff_stock_col}]={row[diff_stock_col]}, row[{diff_vendite_col}]={row[diff_vendite_col]}")
            
            # Aggiorna la riga in values
            values[row_idx-1] = row
        
        # Funzione helper per convertire indice colonna in lettera
        def column_index_to_letter(col_idx):
            """Converte indice colonna (0-based) in lettere (A, B, C, ..., AA, AB, ...)"""
            result = ""
            col_idx += 1  # Converti in 1-based
            while col_idx > 0:
                col_idx -= 1
                result = chr(col_idx % 26 + ord('A')) + result
                col_idx //= 26
            return result
        

        
        # Calcola e aggiungi la riga dei totali con formule
        num_cols = len(header)
        num_rows = len(values)
        
        # Rimuovi eventuale riga Totali precedente
        values = [row for row in values if not (row and row[0] == "Totali")]
        
        # Calcola il numero di righe dati (senza header e senza totali)
        # values contiene: riga 1 (header date), riga 2 (header colonne), righe 3-N (dati)
        # La riga dei totali sarà aggiunta come riga N+1
        start_row = 3  # Prima riga dati
        end_row = len(values)  # Ultima riga dati (prima di aggiungere i totali)
        
        totali_row = ["Totali"]
        
        # Aggiungi formula per la colonna B (Diff Vendite mensile)
        col_b_letter = column_index_to_letter(1)  # Colonna B (indice 1)
        diff_vendite_formula = f"=SOMMA({col_b_letter}{start_row}:{col_b_letter}{end_row})"
        totali_row.append(diff_vendite_formula)
        
        # Aggiungi formula per la colonna C (URL) - vuota
        totali_row.append("")
        
        # Aggiungi formule di somma per tutte le colonne dalla D in poi
        for c in range(3, num_cols):  # Inizia da indice 3 (colonna D)
            col_letter = column_index_to_letter(c)
            formula = f"=SOMMA({col_letter}{start_row}:{col_letter}{end_row})"
            totali_row.append(formula)
        
        values.append(totali_row)
        
        # Scrivi tutte le righe aggiornate
        logger.info(f"Scrittura di {len(values)} righe nella tab {month_name}")
        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f"{month_name}!A1",
            valueInputOption='USER_ENTERED',
            body={'values': values}
        ).execute()
        logger.info("Dati scritti con successo nel foglio")
        
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
        
        logger.info(f"Tab {month_name} aggiornata con i dati del giorno {day} e riga Totali con formule")
        

        
        # Aggiorna i totali mensili delle diff vendite nella seconda colonna
        self.update_monthly_diff_vendite_totals(month_name, year)
        
        self.format_monthly_sheet(month_name, year)
        
        # Aggiorna la tab Overview dopo aver aggiornato la tab mensile
        self.update_overview_sheet()
        
        return True

    def format_only_monthly_sheet(self, month_name: str, year: int):
        """Applica solo la formattazione a una tab mensile già esistente, senza toccare i dati."""
        self.format_monthly_sheet(month_name, year)

    def update_monthly_diff_vendite_totals(self, month_name: str, year: int):
        """Aggiorna la seconda colonna con i totali mensili delle diff vendite."""
        try:
            # Leggi i dati attuali
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{month_name}!A:ZZ"
            ).execute()
            values = result.get('values', [])
            
            if not values or len(values) < 2:
                logger.error(f"Tab {month_name} non ha dati sufficienti")
                return False
            
            # Trova tutte le colonne "diff vendite" dalla riga 2 (header delle colonne)
            diff_vendite_columns = []
            if len(values) > 1:
                header_row = values[1]  # Riga 2 contiene le intestazioni delle colonne
                for col_idx, header in enumerate(header_row):
                    if header and "diff vendite" in str(header).lower():
                        diff_vendite_columns.append(col_idx)
                        logger.info(f"Trovata colonna diff vendite: {col_idx} = '{header}'")
            
            # Se non trova colonne diff vendite, prova a calcolarle dinamicamente
            if not diff_vendite_columns:
                logger.info("Nessuna colonna diff vendite trovata, calcolo dinamico...")
                # Le colonne diff vendite sono ogni 4 colonne a partire dalla colonna 5 (E)
                # Struttura: articoli, vendite, diff stock, diff vendite
                for i in range(5, len(header_row), 4):
                    if i < len(header_row):
                        diff_vendite_columns.append(i)
                        logger.info(f"Aggiunta colonna diff vendite calcolata: {i}")
            
            logger.info(f"Trovate {len(diff_vendite_columns)} colonne diff vendite: {diff_vendite_columns}")
            
            # Per ogni riga profilo (escludi header e totali)
            for row_idx in range(2, len(values)):
                if values[row_idx] and values[row_idx][0] and values[row_idx][0] != "Totali":
                    total_diff_vendite = 0
                    
                    # Calcola la somma delle diff vendite per questo profilo
                    for col_idx in diff_vendite_columns:
                        if col_idx < len(values[row_idx]):
                            try:
                                cell_value = values[row_idx][col_idx]
                                logger.info(f"  Colonna {col_idx}: valore = '{cell_value}'")
                                if cell_value and str(cell_value).strip():
                                    # Rimuovi caratteri non numerici e converti
                                    clean_val = str(cell_value).replace("'", "").replace(" ", "").strip()
                                    if clean_val:
                                        val_int = int(clean_val)
                                        total_diff_vendite += val_int
                                        logger.info(f"    Aggiunto {val_int} al totale (ora = {total_diff_vendite})")
                            except (ValueError, TypeError) as e:
                                logger.warning(f"    Errore nel parsing del valore '{cell_value}': {e}")
                                pass
                    
                    # Aggiorna la seconda colonna (indice 1) - Diff Vendite mensile
                    if len(values[row_idx]) > 1:
                        values[row_idx][1] = total_diff_vendite
                        logger.info(f"Profilo {values[row_idx][0]}: totale diff vendite = {total_diff_vendite}")
            
            # Scrivi i dati aggiornati
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{month_name}!A1",
                valueInputOption='USER_ENTERED',
                body={'values': values}
            ).execute()
            
            logger.info(f"Totali diff vendite mensili aggiornati per {month_name}")
            return True
            
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento dei totali diff vendite mensili: {e}")
            return False

    def create_overview_sheet(self):
        """Crea la tab Overview se non esiste."""
        try:
            # Ottieni lista delle tab
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheet_names = [s['properties']['title'] for s in spreadsheet['sheets']]
            
            if "Overview" not in sheet_names:
                # Crea la tab
                requests = [{
                    "addSheet": {
                        "properties": {
                            "title": "Overview"
                        }
                    }
                }]
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={"requests": requests}
                ).execute()
                logger.info("Tab 'Overview' creata")
            
            return True
            
        except Exception as e:
            logger.error(f"Errore nella creazione della tab Overview: {e}")
            return False

    def update_overview_sheet(self):
        """Aggiorna la tab Overview con tutti i mesi dell'anno, totali di colonna e riga."""
        try:
            # Crea la tab se non esiste
            self.create_overview_sheet()
            
            # Ottieni lista delle tab mensili esistenti
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheet_names = [s['properties']['title'] for s in spreadsheet['sheets']]
            
            # Crea lista completa dei mesi dell'anno
            all_months = [
                'january', 'february', 'march', 'april', 'may', 'june',
                'july', 'august', 'september', 'october', 'november', 'december'
            ]
            
            # Crea le tab mancanti per i mesi futuri
            for month in all_months:
                if month not in sheet_names:
                    logger.info(f"Creazione tab {month} per il futuro")
                    self.create_monthly_tab(month, 2025)
            
            logger.info(f"Tab mensili disponibili: {all_months}")
            
            # Prepara i dati per Overview
            overview_data = []
            
            # Header: Profilo + tutti i mesi + Totale
            header = ["Profilo"] + [month.capitalize() for month in all_months] + ["Totale"]
            overview_data.append(header)
            
            # Ottieni la lista dei profili dalla configurazione
            from config import VESTIAIRE_PROFILES
            profiles = list(VESTIAIRE_PROFILES.keys())
            
            # Leggi tutti i dati delle tab mensili in una volta sola per ridurre le chiamate API
            monthly_data = {}
            for month in all_months:
                try:
                    # Leggi i dati della tab mensile
                    result = self.service.spreadsheets().values().get(
                        spreadsheetId=self.spreadsheet_id,
                        range=f"{month}!A:ZZ"
                    ).execute()
                    values = result.get('values', [])
                    monthly_data[month] = values
                    logger.info(f"Dati {month} caricati: {len(values)} righe")
                    
                    # Delay per evitare rate limit
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Errore nel caricamento dati {month}: {e}")
                    monthly_data[month] = []
            
            # Per ogni profilo, calcola i totali mensili
            for profile in profiles:
                row = [profile]
                profile_total = 0
                
                for month in all_months:
                    try:
                        values = monthly_data.get(month, [])
                        
                        if not values or len(values) < 2:
                            row.append(0)
                            continue
                        
                        # Trova la riga del profilo
                        profile_row = None
                        for row_idx, data_row in enumerate(values):
                            if data_row and data_row[0] == profile:
                                profile_row = data_row
                                break
                        
                        if not profile_row or len(profile_row) < 2:
                            row.append(0)
                            continue
                        
                        # Prendi direttamente il totale dalla colonna B (Diff Vendite [Mese])
                        if len(profile_row) > 1 and profile_row[1] != "":
                            try:
                                total = int(str(profile_row[1]).replace("'", "").replace(" ", "").strip())
                                row.append(total)
                                profile_total += total
                                logger.info(f"  {profile} in {month}: totale = {total} (colonna B)")
                            except (ValueError, TypeError):
                                logger.warning(f"  {profile} in {month}: valore non numerico in colonna B: {profile_row[1]}")
                                row.append(0)
                        else:
                            logger.warning(f"  {profile} in {month}: colonna B vuota o mancante")
                            row.append(0)
                            
                    except Exception as e:
                        logger.error(f"Errore nel calcolo per {profile} in {month}: {e}")
                        row.append(0)
                
                # Aggiungi il totale del profilo
                row.append(profile_total)
                overview_data.append(row)
            
            # Calcola i totali di colonna (per mese)
            column_totals = ["TOTALE"]
            for month_idx in range(len(all_months)):
                month_total = 0
                for row_idx in range(1, len(overview_data)):  # Salta header
                    if len(overview_data[row_idx]) > month_idx + 1:
                        try:
                            month_total += int(str(overview_data[row_idx][month_idx + 1]).replace("'", "").strip())
                        except (ValueError, TypeError):
                            pass
                column_totals.append(month_total)
            
            # Aggiungi il totale generale (somma di tutti i mesi)
            grand_total = sum(column_totals[1:])  # Salta "TOTALE"
            column_totals.append(grand_total)
            
            # Aggiungi la riga dei totali
            overview_data.append(column_totals)
            
            # Scrivi i dati nella tab Overview
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range="Overview!A1",
                valueInputOption='USER_ENTERED',
                body={'values': overview_data}
            ).execute()
            
            # Applica formattazione
            self.format_overview_sheet(len(all_months))
            
            logger.info("Tab Overview aggiornata con successo")
            return True
            
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento della tab Overview: {e}")
            return False

    def format_overview_sheet(self, num_months: int):
        """Applica formattazione alla tab Overview con tutti i mesi e totali."""
        try:
            sheet_id = self._get_sheet_id("Overview")
            
            requests = []
            
            # Formattazione header (tutti i mesi + colonna Totale)
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": num_months + 2  # +2 per Profilo e Totale
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.8},
                            "textFormat": {
                                "bold": True,
                                "foregroundColor": {"red": 1, "green": 1, "blue": 1}
                            }
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)"
                }
            })
            
            # Colori alternati per le righe dati (13 profili)
            for row_idx in range(1, 14):  # 13 profili
                color = {"red": 0.89, "green": 0.94, "blue": 0.99} if row_idx % 2 == 0 else {"red": 1, "green": 1, "blue": 1}
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": row_idx,
                            "endRowIndex": row_idx + 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_months + 2  # +2 per Profilo e Totale
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": color
                            }
                        },
                        "fields": "userEnteredFormat.backgroundColor"
                    }
                })
            
            # Formattazione speciale per la riga dei totali (riga 15)
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 14,  # Riga 15 (indice 14)
                        "endRowIndex": 15,
                        "startColumnIndex": 0,
                        "endColumnIndex": num_months + 2
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.9, "green": 0.4, "blue": 0.4},  # Rosso più tenue
                            "textFormat": {
                                "bold": True,
                                "foregroundColor": {"red": 1, "green": 1, "blue": 1}
                            }
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)"
                }
            })
            
            # Formattazione speciale per la colonna Totale (ultima colonna)
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 15,  # Fino alla riga dei totali
                        "startColumnIndex": num_months + 1,  # Colonna Totale
                        "endColumnIndex": num_months + 2
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.4, "green": 0.9, "blue": 0.4},  # Verde più tenue
                            "textFormat": {
                                "bold": True,
                                "foregroundColor": {"red": 0, "green": 0, "blue": 0}
                            }
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)"
                }
            })
            
            # Larghezza colonne
            for col_idx in range(num_months + 2):  # +2 per Profilo e Totale
                requests.append({
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": col_idx,
                            "endIndex": col_idx + 1
                        },
                        "properties": {"pixelSize": 120},
                        "fields": "pixelSize"
                    }
                })
            
            # Applica formattazione
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={"requests": requests}
            ).execute()
            
            logger.info("Formattazione tab Overview completata")
            
        except Exception as e:
            logger.error(f"Errore nella formattazione della tab Overview: {e}")



def main():
    """Funzione principale per testare l'updater"""
    # Test con dati di esempio
    test_data = [
        {
            "name": "Rediscover",
            "url": "https://it.vestiairecollective.com/profile/2039815/",
            "articles": 573,
            "sales": 7198,
            "timestamp": "2025-01-15 10:00:00"
        },
        {
            "name": "Volodymyr", 
            "url": "https://it.vestiairecollective.com/profile/5924329/",
            "articles": 2315,
            "sales": 5558,
            "timestamp": "2025-01-15 10:00:00"
        }
    ]
    
    print("=== TEST SHEETS UPDATER ===")
    print("Dati di test preparati")
    print("Nota: Per testare completamente, configurare le credenziali Google Sheets")

if __name__ == "__main__":
    main() 