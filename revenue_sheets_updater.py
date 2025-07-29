"""
Revenue Google Sheets Updater
Modulo parallelo per aggiornare Google Sheets con i dati dei ricavi
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

class RevenueSheetsUpdater:
    """Classe parallela per aggiornare Google Sheets con i dati dei ricavi"""
    
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
            logger.info("Servizio Google Sheets per ricavi configurato con successo")
            
        except Exception as e:
            logger.error(f"Errore nella configurazione del servizio Google Sheets: {e}")
            raise
    
    def create_revenue_monthly_tab(self, month_name: str, year: int):
        """Crea la tab mensile per i ricavi se non esiste."""
        try:
            # Ottieni lista delle tab
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheet_names = [s['properties']['title'] for s in spreadsheet['sheets']]
            
            # Nome della tab ricavi: "Revenue_[mese]"
            revenue_tab_name = f"Revenue_{month_name.capitalize()}"
            
            if revenue_tab_name not in sheet_names:
                # Crea la tab
                requests = [{
                    "addSheet": {
                        "properties": {
                            "title": revenue_tab_name
                        }
                    }
                }]
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={"requests": requests}
                ).execute()
                logger.info(f"Tab ricavi '{revenue_tab_name}' creata")
                
                # Prepara intestazioni
                days = calendar.monthrange(year, list(calendar.month_name).index(month_name.capitalize()))[1]
                
                # Riga 1: date (merge da formattazione)
                header1 = ["Profilo", "URL", "Totale Ricavi Mensili"]
                for d in range(1, days+1):
                    header1 += [f"{d} {month_name}", "", ""]
                
                # Riga 2: etichette
                header2 = ["", "", ""]
                for d in range(1, days+1):
                    header2 += ["articoli venduti", "ricavi giornalieri", "diff ricavi"]
                
                # Scrivi intestazioni
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{revenue_tab_name}!A1",
                    valueInputOption='USER_ENTERED',
                    body={'values': [header1, header2]}
                ).execute()
                logger.info(f"Intestazioni ricavi scritte su '{revenue_tab_name}'")
                
                # Applica formattazione
                self.format_revenue_monthly_sheet(revenue_tab_name, year)
                
            return revenue_tab_name
            
        except Exception as e:
            logger.error(f"Errore nella creazione tab ricavi mensile: {e}")
            return None
    
    def format_revenue_monthly_sheet(self, tab_name: str, year: int):
        """Formatta la tab mensile dei ricavi: merge celle, header, colori alternati, larghezza colonne."""
        try:
            # Ottieni il mese dal nome della tab
            month_name = tab_name.replace("Revenue_", "").lower()
            days = calendar.monthrange(year, list(calendar.month_name).index(month_name.capitalize()))[1]
            
            # Merge celle riga 1 per ogni giorno
            requests = []
            sheet_id = self._get_sheet_id(tab_name)
            logger.info(f"[FORMAT REVENUE] sheet_id trovato per '{tab_name}': {sheet_id}")
            
            # Calcola il numero di righe dati (senza la riga Totali)
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{tab_name}!A:ZZ"
            ).execute()
            values = result.get('values', [])
            num_data_rows = len(values) - 1 if values and values[-1][0] == "Totali" else len(values)
            end_row = num_data_rows
            logger.info(f"[FORMAT REVENUE] Colori alternati fino a riga: {end_row}")
            
            start_col = 3  # +3 perché ora abbiamo Profilo, URL, Totale Ricavi Mensili
            for d in range(1, days+1):
                end_col = start_col + 2  # 3 colonne per giorno: articoli, ricavi, diff
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
            start_col = 3
            for d in range(1, days+1):
                end_col = start_col + 2
                color = {"red": 0.89, "green": 0.94, "blue": 0.99} if d % 2 == 0 else {"red": 1, "green": 1, "blue": 1}
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": end_row,
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
            for c in range(3, 3+days*3):
                requests.append({
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": c,
                            "endIndex": c+1
                        },
                        "properties": {"pixelSize": 80},
                        "fields": "pixelSize"
                    }
                })
            
            logger.info(f"[FORMAT REVENUE] Numero richieste batch da inviare: {len(requests)}")
            
            # Applica richieste
            resp = self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={"requests": requests}
            ).execute()
            logger.info(f"[FORMAT REVENUE] Risposta batchUpdate: {resp}")
            logger.info(f"Formattazione tab ricavi {tab_name} completata")
            
        except Exception as e:
            logger.error(f"Errore nella formattazione tab ricavi mensile: {e}")
    
    def _get_sheet_id(self, sheet_name: str):
        """Ottiene l'ID della tab specificata"""
        spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
        for s in spreadsheet['sheets']:
            if s['properties']['title'] == sheet_name:
                return s['properties']['sheetId']
        raise Exception(f"Sheet {sheet_name} non trovato")
    
    def update_revenue_monthly_sheet(self, revenue_data: list, year: int, month: int, day: int):
        """Aggiorna la tab mensile dei ricavi con i dati del giorno, calcolando le differenze."""
        import copy
        
        month_name = calendar.month_name[month].lower()
        revenue_tab_name = self.create_revenue_monthly_tab(month_name, year)
        
        if not revenue_tab_name:
            logger.error(f"Impossibile creare/ottenere la tab ricavi per {month_name}")
            return False
        
        # Leggi dati attuali
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=f"{revenue_tab_name}!A:ZZ"
        ).execute()
        values = result.get('values', [])
        
        if not values:
            logger.error(f"Tab ricavi {revenue_tab_name} vuota!")
            return False
        
        header = values[0]
        
        # Mappa profilo->riga
        profilo_to_row = {row[0]: i for i, row in enumerate(values[1:], start=2) if row and row[0]}
        
        # Rimuovi profili che non sono più nella configurazione
        profili_configurati = {profilo['name'] for profilo in revenue_data}
        logger.info(f"Profili ricavi configurati: {profili_configurati}")
        
        righe_da_rimuovere = []
        for i, row in enumerate(values[1:], start=1):
            if row and row[0] and row[0] not in profili_configurati and row[0] != "Totali":
                righe_da_rimuovere.append(i)
                logger.info(f"Trovato profilo ricavi da rimuovere: {row[0]} (riga {i})")
        
        logger.info(f"Righe ricavi da rimuovere: {righe_da_rimuovere}")
        
        # Rimuovi le righe in ordine inverso per non alterare gli indici
        for i in sorted(righe_da_rimuovere, reverse=True):
            if i < len(values):
                profilo_rimosso = values[i][0] if i < len(values) else 'Unknown'
                del values[i]
                logger.info(f"Rimosso profilo ricavi obsoleto: {profilo_rimosso}")
        
        # Ricostruisci la mappa profilo->riga dopo la rimozione
        profilo_to_row = {row[0]: i for i, row in enumerate(values[1:], start=2) if row and row[0]}
        
        # Calcola colonne da aggiornare
        # Struttura: Profilo, URL, Totale Ricavi Mensili, [colonne nascoste], dati giornalieri
        base_col = 51 + (day-13)*3  # 3 colonne per giorno: articoli, ricavi, diff
        articoli_col = base_col
        ricavi_col = base_col+1
        diff_ricavi_col = base_col+2
        
        # Prepara update
        updates = []
        for profilo in revenue_data:
            name = profilo['name']
            url = profilo['url']
            sold_items = profilo['sold_items_count']
            revenue = profilo['total_revenue']
            
            # Trova riga
            if name in profilo_to_row:
                row_idx = profilo_to_row[name]
                row = copy.deepcopy(values[row_idx-1]) if row_idx-1 < len(values) else [name, url, ""]
            else:
                # Nuovo profilo
                row = [name, url, ""] + ["" for _ in range(len(header)-3)]
                values.append(row)
                row_idx = len(values)
                profilo_to_row[name] = row_idx
            
            # Aggiorna sempre l'URL nella colonna B (indice 1)
            if len(row) > 1:
                row[1] = url
            
            # Calcola differenze
            prev_revenue = None
            if day > 13:  # Solo se non è il primo giorno
                prev_revenue_col = 52 + (day-14)*3  # Giorno precedente
                
                if prev_revenue_col < len(row):
                    try:
                        if row[prev_revenue_col]:
                            clean_val = str(row[prev_revenue_col]).replace("'", "").replace(" ", "").strip()
                            prev_revenue = float(clean_val) if clean_val else None
                        else:
                            prev_revenue = None
                    except (ValueError, TypeError):
                        prev_revenue = None
            
            # Calcolo normale per tutti i casi
            diff_revenue = revenue - prev_revenue if prev_revenue is not None else ""
            
            # Allunga la riga se serve
            while len(row) < diff_ricavi_col+1:
                row.append("")
            
            row[articoli_col] = sold_items
            row[ricavi_col] = revenue
            row[diff_ricavi_col] = diff_revenue if diff_revenue != "" else ""
            
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
        
        # Calcola il numero di righe dati
        start_row = 3  # Prima riga dati
        end_row = len(values)  # Ultima riga dati
        
        totali_row = ["Totali"]
        
        # Aggiungi formula per la colonna C (Totale Ricavi Mensili)
        col_c_letter = column_index_to_letter(2)  # Colonna C (indice 2)
        total_revenue_formula = f"=SOMMA({col_c_letter}{start_row}:{col_c_letter}{end_row})"
        totali_row.append("")  # URL vuoto
        totali_row.append(total_revenue_formula)
        
        # Aggiungi formule di somma per tutte le colonne dalla D in poi
        for c in range(3, num_cols):
            col_letter = column_index_to_letter(c)
            formula = f"=SOMMA({col_letter}{start_row}:{col_letter}{end_row})"
            totali_row.append(formula)
        
        values.append(totali_row)
        
        # Scrivi tutte le righe aggiornate
        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f"{revenue_tab_name}!A1",
            valueInputOption='USER_ENTERED',
            body={'values': values}
        ).execute()
        
        # Applica sfondo grigio chiaro alla riga Totali
        try:
            sheet_id = self._get_sheet_id(revenue_tab_name)
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
            logger.error(f"Errore nella formattazione della riga Totali ricavi: {e}")
        
        # Aggiorna i totali mensili dei ricavi nella terza colonna
        self.update_monthly_revenue_totals(revenue_tab_name, year)
        
        # Applica formattazione
        self.format_revenue_monthly_sheet(revenue_tab_name, year)
        
        # Aggiorna la tab Overview ricavi
        self.update_revenue_overview_sheet()
        
        logger.info(f"Tab ricavi {revenue_tab_name} aggiornata con i dati del giorno {day}")
        return True
    
    def update_monthly_revenue_totals(self, tab_name: str, year: int):
        """Aggiorna la terza colonna con i totali mensili dei ricavi."""
        try:
            # Leggi i dati attuali
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{tab_name}!A:ZZ"
            ).execute()
            values = result.get('values', [])
            
            if not values or len(values) < 2:
                logger.error(f"Tab ricavi {tab_name} non ha dati sufficienti")
                return False
            
            # Trova tutte le colonne "ricavi giornalieri" dalla riga 2
            revenue_columns = []
            if len(values) > 1:
                header_row = values[1]
                for col_idx, header in enumerate(header_row):
                    if header and "ricavi giornalieri" in str(header).lower():
                        revenue_columns.append(col_idx)
            
            logger.info(f"Trovate {len(revenue_columns)} colonne ricavi: {revenue_columns}")
            
            # Per ogni riga profilo (escludi header e totali)
            for row_idx in range(2, len(values)):
                if values[row_idx] and values[row_idx][0] and values[row_idx][0] != "Totali":
                    total_monthly_revenue = 0.0
                    
                    # Calcola la somma dei ricavi per questo profilo
                    for col_idx in revenue_columns:
                        if col_idx < len(values[row_idx]):
                            try:
                                cell_value = values[row_idx][col_idx]
                                if cell_value and str(cell_value).strip():
                                    clean_val = str(cell_value).replace("'", "").replace(" ", "").strip()
                                    if clean_val:
                                        total_monthly_revenue += float(clean_val)
                            except (ValueError, TypeError):
                                pass
                    
                    # Aggiorna la terza colonna (indice 2) - Totale Ricavi Mensili
                    if len(values[row_idx]) > 2:
                        values[row_idx][2] = total_monthly_revenue
                        logger.info(f"Profilo {values[row_idx][0]}: totale ricavi mensili = €{total_monthly_revenue:.2f}")
            
            # Scrivi i dati aggiornati
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{tab_name}!A1",
                valueInputOption='USER_ENTERED',
                body={'values': values}
            ).execute()
            
            logger.info(f"Totali ricavi mensili aggiornati per {tab_name}")
            return True
            
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento dei totali ricavi mensili: {e}")
            return False
    
    def create_revenue_overview_sheet(self):
        """Crea la tab Overview Ricavi se non esiste."""
        try:
            # Ottieni lista delle tab
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheet_names = [s['properties']['title'] for s in spreadsheet['sheets']]
            
            if "Revenue_Overview" not in sheet_names:
                # Crea la tab
                requests = [{
                    "addSheet": {
                        "properties": {
                            "title": "Revenue_Overview"
                        }
                    }
                }]
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={"requests": requests}
                ).execute()
                logger.info("Tab 'Revenue_Overview' creata")
            
            return True
            
        except Exception as e:
            logger.error(f"Errore nella creazione della tab Revenue_Overview: {e}")
            return False
    
    def update_revenue_overview_sheet(self):
        """Aggiorna la tab Revenue_Overview con i totali mensili dei ricavi."""
        try:
            # Crea la tab se non esiste
            self.create_revenue_overview_sheet()
            
            # Ottieni lista delle tab ricavi mensili esistenti
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheet_names = [s['properties']['title'] for s in spreadsheet['sheets']]
            
            # Filtra solo le tab ricavi mensili
            revenue_month_names = []
            for name in sheet_names:
                if name.startswith("Revenue_") and name != "Revenue_Overview":
                    month_name = name.replace("Revenue_", "").lower()
                    if month_name in [calendar.month_name[i].lower() for i in range(1, 13)]:
                        revenue_month_names.append(month_name)
            
            # Ordina le tab mensili cronologicamente
            revenue_month_names.sort(key=lambda x: list(calendar.month_name).index(x.capitalize()))
            
            logger.info(f"Tab ricavi mensili trovate: {revenue_month_names}")
            
            # Prepara i dati per Revenue_Overview
            overview_data = []
            
            # Header: Profilo + mesi
            header = ["Profilo"] + [month.capitalize() for month in revenue_month_names]
            overview_data.append(header)
            
            # Ottieni la lista dei profili dalla configurazione
            from config import VESTIAIRE_PROFILES
            profiles = list(VESTIAIRE_PROFILES.keys())
            
            # Per ogni profilo, calcola i totali mensili
            for profile in profiles:
                row = [profile]
                
                for month in revenue_month_names:
                    try:
                        # Leggi i dati della tab ricavi mensile
                        revenue_tab_name = f"Revenue_{month.capitalize()}"
                        result = self.service.spreadsheets().values().get(
                            spreadsheetId=self.spreadsheet_id,
                            range=f"{revenue_tab_name}!A:ZZ"
                        ).execute()
                        values = result.get('values', [])
                        
                        if not values or len(values) < 2:
                            row.append(0)
                            continue
                        
                        # Trova la riga del profilo
                        profile_row = None
                        for row_idx, data_row in enumerate(values):
                            if data_row and data_row[0] == profile:
                                profile_row = data_row
                                break
                        
                        if not profile_row or len(profile_row) < 3:
                            row.append(0)
                            continue
                        
                        # Prendi il valore dalla terza colonna (totale ricavi mensile)
                        if len(profile_row) > 2 and profile_row[2] != "":
                            try:
                                total = float(str(profile_row[2]).replace("'", "").replace(" ", "").strip())
                                row.append(total)
                            except (ValueError, TypeError):
                                row.append(0)
                        else:
                            row.append(0)
                            
                    except Exception as e:
                        logger.error(f"Errore nel calcolo ricavi per {profile} in {month}: {e}")
                        row.append(0)
                
                overview_data.append(row)
            
            # Scrivi i dati nella tab Revenue_Overview
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range="Revenue_Overview!A1",
                valueInputOption='USER_ENTERED',
                body={'values': overview_data}
            ).execute()
            
            # Applica formattazione
            self.format_revenue_overview_sheet(len(revenue_month_names))
            
            logger.info("Tab Revenue_Overview aggiornata con successo")
            return True
            
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento della tab Revenue_Overview: {e}")
            return False
    
    def format_revenue_overview_sheet(self, num_months: int):
        """Applica formattazione alla tab Revenue_Overview."""
        try:
            sheet_id = self._get_sheet_id("Revenue_Overview")
            
            requests = []
            
            # Formattazione header
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": num_months + 1
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.2, "green": 0.8, "blue": 0.2},  # Verde per ricavi
                            "textFormat": {
                                "bold": True,
                                "foregroundColor": {"red": 1, "green": 1, "blue": 1}
                            }
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)"
                }
            })
            
            # Colori alternati per le righe dati
            for row_idx in range(1, 14):  # 13 profili
                color = {"red": 0.89, "green": 0.94, "blue": 0.99} if row_idx % 2 == 0 else {"red": 1, "green": 1, "blue": 1}
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": row_idx,
                            "endRowIndex": row_idx + 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_months + 1
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": color
                            }
                        },
                        "fields": "userEnteredFormat.backgroundColor"
                    }
                })
            
            # Larghezza colonne
            for col_idx in range(num_months + 1):
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
            
            logger.info("Formattazione tab Revenue_Overview completata")
            
        except Exception as e:
            logger.error(f"Errore nella formattazione della tab Revenue_Overview: {e}")

def main():
    """Funzione principale per testare l'updater ricavi"""
    # Test con dati di esempio
    test_data = [
        {
            "name": "Rediscover",
            "url": "https://it.vestiairecollective.com/profile/2039815/",
            "sold_items_count": 15,
            "total_revenue": 2500.50,
            "timestamp": "2024-01-15 10:00:00"
        },
        {
            "name": "Volodymyr", 
            "url": "https://it.vestiairecollective.com/profile/5924329/",
            "sold_items_count": 8,
            "total_revenue": 1200.75,
            "timestamp": "2024-01-15 10:00:00"
        }
    ]
    
    print("=== TEST REVENUE SHEETS UPDATER ===")
    print("Dati di test preparati")
    print("Nota: Per testare completamente, configurare le credenziali Google Sheets")

if __name__ == "__main__":
    main() 