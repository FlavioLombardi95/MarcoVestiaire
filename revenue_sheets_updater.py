#!/usr/bin/env python3
"""
Revenue Sheets Updater - Aggiornamento Google Sheets
Gestione avanzata di Google Sheets con formattazione e metriche
"""

import os
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    logging.error(f"❌ Dipendenze Google API mancanti: {e}")
    logging.error("   Installa: pip install google-api-python-client google-auth google-auth-oauthlib")

# Configurazione
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID', 'your-spreadsheet-id-here')

logger = logging.getLogger(__name__)

class RevenueSheetsUpdater:
    """Gestore aggiornamento Google Sheets per Revenue Analysis"""
    
    def __init__(self):
        """Inizializza il gestore Google Sheets"""
        self.service = None
        self.spreadsheet_id = SPREADSHEET_ID
        self._authenticate()
    
    def _authenticate(self):
        """Autenticazione Google Sheets API"""
        try:
            creds = None
            
            # Controlla se esistono credenziali salvate
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
            # Se non ci sono credenziali valide, richiedi l'autorizzazione
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # Cerca il file credentials.json
                    credentials_file = 'credentials.json'
                    if not os.path.exists(credentials_file):
                        # Cerca in vari percorsi comuni
                        possible_paths = [
                            'google_credentials.json',
                            '.credentials.json',
                            'config/credentials.json',
                            '../credentials.json'
                        ]
                        
                        for path in possible_paths:
                            if os.path.exists(path):
                                credentials_file = path
                                break
                    
                    if os.path.exists(credentials_file):
                        flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                        creds = flow.run_local_server(port=0)
                        
                        # Salva le credenziali per il prossimo utilizzo
                        with open('token.json', 'w') as token:
                            token.write(creds.to_json())
                    else:
                        logger.error("❌ File credentials.json non trovato")
                        logger.error("   Scarica le credenziali da Google Cloud Console")
                        return
            
            # Costruisci il servizio
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("✅ Autenticazione Google Sheets riuscita")
            
        except Exception as e:
            logger.error(f"❌ Errore autenticazione Google Sheets: {e}")
            self.service = None
    
    def _test_connection(self) -> bool:
        """Test connessione Google Sheets"""
        try:
            if not self.service:
                logger.error("❌ Servizio Google Sheets non inizializzato")
                return False
            
            # Test lettura spreadsheet
            result = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            logger.info(f"✅ Connessione Google Sheets riuscita: {result.get('properties', {}).get('title', 'Unknown')}")
            return True
            
        except HttpError as e:
            logger.error(f"❌ Errore HTTP Google Sheets: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Errore connessione Google Sheets: {e}")
            return False
    
    def _create_monthly_tab(self, month_year: str) -> bool:
        """Crea una nuova tab mensile con formattazione"""
        try:
            logger.info(f"📊 Creazione tab mensile: {month_year}")
            
            # Prepara i dati della tab
            headers = [
                'Data', 'Profilo', 'Articoli Venduti', 'Ricavi (€)', 
                'Ricavi Cumulativi (€)', 'Note'
            ]
            
            # Crea la tab
            request = {
                'addSheet': {
                    'properties': {
                        'title': month_year,
                        'gridProperties': {
                            'rowCount': 1000,
                            'columnCount': len(headers)
                        }
                    }
                }
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': [request]}
            ).execute()
            
            # Inserisci headers
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{month_year}!A1:F1",
                valueInputOption='RAW',
                body={'values': [headers]}
            ).execute()
            
            # Applica formattazione headers
            self._format_headers(month_year)
            
            logger.info(f"✅ Tab {month_year} creata con successo")
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore creazione tab {month_year}: {e}")
            return False
    
    def _format_headers(self, sheet_name: str):
        """Applica formattazione agli headers"""
        try:
            # Formattazione headers (verde)
            header_format = {
                'backgroundColor': {
                    'red': 0.2,
                    'green': 0.8,
                    'blue': 0.2
                },
                'textFormat': {
                    'bold': True,
                    'fontSize': 12
                },
                'horizontalAlignment': 'CENTER'
            }
            
            request = {
                'repeatCell': {
                    'range': {
                        'sheetId': self._get_sheet_id(sheet_name),
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': 6
                    },
                    'cell': {
                        'userEnteredFormat': header_format
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
                }
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': [request]}
            ).execute()
            
        except Exception as e:
            logger.warning(f"⚠️ Errore formattazione headers: {e}")
    
    def _get_sheet_id(self, sheet_name: str) -> Optional[int]:
        """Ottiene l'ID della sheet per nome"""
        try:
            result = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            for sheet in result.get('sheets', []):
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Errore ottenimento sheet ID: {e}")
            return None
    
    def _add_revenue_data(self, sheet_name: str, data: List[List]) -> bool:
        """Aggiunge dati di revenue alla tab"""
        try:
            if not data:
                logger.warning("⚠️ Nessun dato da aggiungere")
                return True
            
            # Trova la prossima riga vuota
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A:A"
            ).execute()
            
            next_row = len(result.get('values', [])) + 1
            
            # Inserisci i dati
            range_name = f"{sheet_name}!A{next_row}:F{next_row + len(data) - 1}"
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': data}
            ).execute()
            
            # Applica formattazione alternata
            self._apply_alternating_colors(sheet_name, next_row, len(data))
            
            logger.info(f"✅ Dati aggiunti alla tab {sheet_name}: {len(data)} righe")
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore aggiunta dati: {e}")
            return False
    
    def _apply_alternating_colors(self, sheet_name: str, start_row: int, num_rows: int):
        """Applica colori alternati alle righe"""
        try:
            # Colori alternati
            color1 = {'red': 0.95, 'green': 0.95, 'blue': 0.95}  # Grigio chiaro
            color2 = {'red': 1.0, 'green': 1.0, 'blue': 1.0}     # Bianco
            
            requests = []
            
            for i in range(num_rows):
                row_index = start_row + i - 1
                color = color1 if i % 2 == 0 else color2
                
                request = {
                    'repeatCell': {
                        'range': {
                            'sheetId': self._get_sheet_id(sheet_name),
                            'startRowIndex': row_index,
                            'endRowIndex': row_index + 1,
                            'startColumnIndex': 0,
                            'endColumnIndex': 6
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'backgroundColor': color
                            }
                        },
                        'fields': 'userEnteredFormat.backgroundColor'
                    }
                }
                requests.append(request)
            
            if requests:
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': requests}
                ).execute()
                
        except Exception as e:
            logger.warning(f"⚠️ Errore formattazione colori: {e}")
    
    def update_revenue_sheets(self, results: Dict) -> bool:
        """Aggiorna Google Sheets con i risultati del revenue analysis"""
        try:
            if not self.service:
                logger.error("❌ Servizio Google Sheets non disponibile")
                return False
            
            logger.info("📊 Aggiornamento Google Sheets...")
            
            # Determina il mese corrente
            current_month = datetime.now().strftime("%Y-%m")
            sheet_name = f"Revenue_{current_month}"
            
            # Controlla se la tab esiste, altrimenti creala
            try:
                self.service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{sheet_name}!A1"
                ).execute()
            except HttpError:
                # Tab non esiste, creala
                if not self._create_monthly_tab(sheet_name):
                    return False
            
            # Prepara i dati per l'inserimento
            today = datetime.now().strftime("%Y-%m-%d")
            data_to_insert = []
            
            total_revenue = 0
            total_items = 0
            
            for profile_name, result in results.items():
                items_sold = result.get('items_sold', 0)
                revenue = result.get('revenue', 0.0)
                
                total_revenue += revenue
                total_items += items_sold
                
                row_data = [
                    today,
                    profile_name,
                    items_sold,
                    f"{revenue:.2f}",
                    f"{total_revenue:.2f}",
                    "OK" if revenue > 0 else "No prezzi"
                ]
                
                data_to_insert.append(row_data)
            
            # Aggiungi riga totale
            if data_to_insert:
                total_row = [
                    today,
                    "TOTALE",
                    total_items,
                    f"{total_revenue:.2f}",
                    f"{total_revenue:.2f}",
                    f"{len(results)} profili"
                ]
                data_to_insert.append(total_row)
            
            # Inserisci i dati
            success = self._add_revenue_data(sheet_name, data_to_insert)
            
            if success:
                logger.info(f"✅ Google Sheets aggiornato: {len(data_to_insert)} righe")
                logger.info(f"📊 Totale ricavi: €{total_revenue:.2f}")
                logger.info(f"📦 Totale articoli: {total_items}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Errore aggiornamento Google Sheets: {e}")
            return False
    
    def create_revenue_overview(self) -> bool:
        """Crea tab Revenue_Overview con aggregazione mensile"""
        try:
            logger.info("📊 Creazione tab Revenue_Overview...")
            
            # Crea la tab se non esiste
            try:
                self.service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range="Revenue_Overview!A1"
                ).execute()
            except HttpError:
                # Tab non esiste, creala
                headers = [
                    'Mese', 'Profili Analizzati', 'Articoli Totali', 
                    'Ricavi Totali (€)', 'Media per Profilo (€)', 'Note'
                ]
                
                request = {
                    'addSheet': {
                        'properties': {
                            'title': 'Revenue_Overview',
                            'gridProperties': {
                                'rowCount': 100,
                                'columnCount': len(headers)
                            }
                        }
                    }
                }
                
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body={'requests': [request]}
                ).execute()
                
                # Inserisci headers
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range="Revenue_Overview!A1:F1",
                    valueInputOption='RAW',
                    body={'values': [headers]}
                ).execute()
                
                # Formatta headers
                self._format_headers("Revenue_Overview")
            
            logger.info("✅ Tab Revenue_Overview creata/aggiornata")
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore creazione Revenue_Overview: {e}")
            return False 