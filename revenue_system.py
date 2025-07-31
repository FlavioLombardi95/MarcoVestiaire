#!/usr/bin/env python3
"""
Revenue System - Sistema essenziale per aggiornamento ricavi
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, List
import json
import calendar
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from config import VESTIAIRE_PROFILES as PROFILES
from revenue_scraper import RevenueScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_credentials() -> Dict:
    """Carica credenziali Google Sheets"""
    try:
        credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
        if credentials_json:
            return json.loads(credentials_json)
        
        credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE')
        if credentials_file and os.path.exists(credentials_file):
            with open(credentials_file, 'r') as f:
                return json.load(f)
        
        possible_files = ["vestiaire-monitor-ba3e8b6417eb.json", "credentials.json"]
        for filename in possible_files:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    return json.load(f)
        
        raise FileNotFoundError("Nessun file di credenziali trovato")
        
    except Exception as e:
        logger.error(f"Errore credenziali: {e}")
        raise

class RevenueSheetsUpdater:
    """Aggiornamento Google Sheets per ricavi"""
    
    def __init__(self, credentials_json: str = None):
        self.spreadsheet_id = "1sWmvdbEgzLCyaNk5XRDHOFTA5KY1RGeMBIqouXvPJ34"
        self.service = None
        
        if credentials_json:
            self.setup_service(credentials_json)
    
    def setup_service(self, credentials_json: str):
        """Configura servizio Google Sheets"""
        try:
            if isinstance(credentials_json, str):
                credentials_dict = json.loads(credentials_json)
            else:
                credentials_dict = credentials_json
            
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            credentials = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
            self.service = build('sheets', 'v4', credentials=credentials)
            
        except Exception as e:
            logger.error(f"Errore Google Sheets: {e}")
            raise
    
    def create_revenue_monthly_tab(self, month_name: str, year: int):
        """Crea tab mensile se non esiste"""
        try:
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheet_names = [s['properties']['title'] for s in spreadsheet['sheets']]
            
            revenue_tab_name = f"Revenue_{month_name.capitalize()}"
            
            if revenue_tab_name not in sheet_names:
                requests = [{"addSheet": {"properties": {"title": revenue_tab_name}}}]
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={"requests": requests}
                ).execute()
                
                # Intestazioni
                days = calendar.monthrange(year, list(calendar.month_name).index(month_name.capitalize()))[1]
                header1 = ["Profilo", "URL", "Totale Ricavi Mensili"]
                header2 = ["", "", ""]
                
                for d in range(1, days+1):
                    header1 += [f"{d} {month_name}", "", ""]
                    header2 += ["articoli venduti", "ricavi giornalieri", "diff ricavi"]
                
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{revenue_tab_name}!A1",
                    valueInputOption='USER_ENTERED',
                    body={'values': [header1, header2]}
                ).execute()
                
            return revenue_tab_name
            
        except Exception as e:
            logger.error(f"Errore creazione tab: {e}")
            raise
    
    def _column_index_to_letter(self, col_idx):
        """Converte indice colonna in lettera"""
        result = ""
        while col_idx > 0:
            col_idx, remainder = divmod(col_idx - 1, 26)
            result = chr(65 + remainder) + result
        return result
    
    def update_revenue_monthly_sheet(self, revenue_data: list, year: int, month: int, day: int):
        """Aggiorna tab mensile con dati del giorno"""
        try:
            month_name = calendar.month_name[month]
            tab_name = f"Revenue_{month_name}"
            
            self.create_revenue_monthly_tab(month_name, year)
            
            # Ottieni dati esistenti
            try:
                existing_data = self.service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{tab_name}!A:C"
                ).execute().get('values', [])
            except:
                existing_data = []
            
            # Aggiorna dati
            update_data = []
            
            for profile_data in revenue_data:
                profile_name = profile_data['name']
                profile_id = profile_data['profile_id']
                sold_count = profile_data['sold_items_count']
                total_revenue = profile_data['total_revenue']
                profile_url = f"https://it.vestiairecollective.com/profile/{profile_id}/"
                
                # Cerca riga esistente
                existing_row = None
                for i, row in enumerate(existing_data):
                    if len(row) > 0 and row[0] == profile_name:
                        existing_row = i
                        break
                
                if existing_row is not None:
                    # Aggiorna riga esistente
                    row_num = existing_row + 1
                    col_letter = self._column_index_to_letter(3 + ((day - 1) * 3))
                    
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=f"{tab_name}!{col_letter}{row_num}",
                        valueInputOption='USER_ENTERED',
                        body={'values': [[sold_count]]}
                    ).execute()
                    
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=f"{tab_name}!{self._column_index_to_letter(3 + ((day - 1) * 3) + 1)}{row_num}",
                        valueInputOption='USER_ENTERED',
                        body={'values': [[total_revenue]]}
                    ).execute()
                    
                else:
                    # Crea nuova riga
                    days_in_month = calendar.monthrange(year, month)[1]
                    new_row = [profile_name, profile_url, ""]
                    
                    for d in range(1, days_in_month + 1):
                        if d == day:
                            new_row.extend([sold_count, total_revenue, ""])
                        else:
                            new_row.extend(["", "", ""])
                    
                    update_data.append(new_row)
            
            # Aggiungi nuove righe
            if update_data:
                self.service.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{tab_name}!A1",
                    valueInputOption='USER_ENTERED',
                    insertDataOption='INSERT_ROWS',
                    body={'values': update_data}
                ).execute()
            
            # Aggiorna totali mensili
            self.update_monthly_revenue_totals(tab_name, year)
            
            logger.info(f"Aggiornamento completato per {day} {month_name} {year}")
            
        except Exception as e:
            logger.error(f"Errore aggiornamento: {e}")
            raise
    
    def update_monthly_revenue_totals(self, tab_name: str, year: int):
        """Aggiorna totali mensili"""
        try:
            data = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{tab_name}!A:ZZ"
            ).execute().get('values', [])
            
            if len(data) < 3:
                return
            
            for row_idx in range(2, len(data)):
                if len(data[row_idx]) < 3:
                    continue
                
                total_revenue = 0
                
                for col_idx in range(5, len(data[row_idx]), 3):
                    if col_idx < len(data[row_idx]) and data[row_idx][col_idx]:
                        try:
                            daily_revenue = float(data[row_idx][col_idx])
                            total_revenue += daily_revenue
                        except:
                            continue
                
                if total_revenue > 0:
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=f"{tab_name}!C{row_idx + 1}",
                        valueInputOption='USER_ENTERED',
                        body={'values': [[total_revenue]]}
                    ).execute()
            
        except Exception as e:
            logger.error(f"Errore totali: {e}")

def main():
    """Funzione principale"""
    logger.info("Avvio aggiornamento Revenue")
    
    try:
        # Carica credenziali
        credentials = load_credentials()
        
        # Inizializza componenti
        sheets_updater = RevenueSheetsUpdater(credentials)
        
        # Ottieni dati vendite esistenti
        existing_sales_data = {}
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from scraper import get_existing_sales_data
            existing_sales_data = get_existing_sales_data()
        except ImportError:
            pass
        
        # Inizializza scraper
        scraper = RevenueScraper(profiles=PROFILES, existing_sales_data=existing_sales_data)
        
        # Esegui scraping
        results = scraper.scrape_all_profiles_revenue()
        
        # Filtra risultati validi
        valid_results = [r for r in results if r['success']]
        logger.info(f"Scraping completato: {len(valid_results)}/{len(results)} profili validi")
        
        if not valid_results:
            logger.error("Nessun risultato valido")
            return
        
        # Aggiorna Google Sheets
        current_date = datetime.now()
        sheets_updater.update_revenue_monthly_sheet(
            valid_results, 
            current_date.year, 
            current_date.month, 
            current_date.day
        )
        
        logger.info("Aggiornamento Revenue completato!")
        
    except Exception as e:
        logger.error(f"Errore sistema revenue: {e}")

if __name__ == "__main__":
    main() 