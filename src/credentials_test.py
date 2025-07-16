#!/usr/bin/env python3
"""
Sistema di test per le credenziali Google Sheets
Diagnostica problemi di connessione e permessi
"""

import os
import sys
import json
import logging
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CredentialsTest:
    """Test delle credenziali Google Sheets"""
    
    def __init__(self):
        self.spreadsheet_id = "1sWmvdbEgzLCyaNk5XRDHOFTA5KY1RGeMBIqouXvPJ34"
        self.service = None
        
    def test_credentials(self, credentials_json: str) -> bool:
        """Test completo delle credenziali"""
        logger.info("🔍 AVVIO TEST CREDENZIALI GOOGLE SHEETS")
        logger.info("=" * 50)
        
        try:
            # Parse credenziali
            logger.info("1️⃣ Parsing credenziali...")
            if isinstance(credentials_json, str):
                credentials_dict = json.loads(credentials_json)
            else:
                credentials_dict = credentials_json
                
            # Verifica campi obbligatori
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
            for field in required_fields:
                if field not in credentials_dict:
                    logger.error(f"❌ Campo mancante nelle credenziali: {field}")
                    return False
                    
            logger.info("✅ Credenziali parsate correttamente")
            logger.info(f"   - Type: {credentials_dict.get('type')}")
            logger.info(f"   - Project ID: {credentials_dict.get('project_id')}")
            logger.info(f"   - Client Email: {credentials_dict.get('client_email')}")
            
            # Crea le credenziali
            logger.info("2️⃣ Creazione credenziali...")
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            credentials = Credentials.from_service_account_info(
                credentials_dict, scopes=scopes
            )
            logger.info("✅ Credenziali create correttamente")
            
            # Configura servizio
            logger.info("3️⃣ Configurazione servizio Google Sheets...")
            self.service = build('sheets', 'v4', credentials=credentials)
            logger.info("✅ Servizio configurato correttamente")
            
            # Test connessione base
            logger.info("4️⃣ Test connessione base...")
            try:
                spreadsheet = self.service.spreadsheets().get(
                    spreadsheetId=self.spreadsheet_id
                ).execute()
                logger.info("✅ Connessione al foglio riuscita")
                logger.info(f"   - Titolo: {spreadsheet.get('properties', {}).get('title')}")
                logger.info(f"   - Sheets: {len(spreadsheet.get('sheets', []))}")
            except HttpError as e:
                logger.error(f"❌ Errore nella connessione: {e}")
                if e.resp.status == 403:
                    logger.error("💡 Possibili cause:")
                    logger.error("   - Service account non ha accesso al foglio")
                    logger.error("   - Foglio non condiviso con l'email del service account")
                    logger.error(f"   - Verifica che {credentials_dict.get('client_email')} sia condiviso")
                return False
            
            # Test lettura
            logger.info("5️⃣ Test lettura dati...")
            try:
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range='A1:B2'
                ).execute()
                values = result.get('values', [])
                logger.info(f"✅ Lettura riuscita: {len(values)} righe")
            except HttpError as e:
                logger.error(f"❌ Errore nella lettura: {e}")
                return False
                
            # Test scrittura
            logger.info("6️⃣ Test scrittura dati...")
            try:
                test_data = [['Test', datetime.now().strftime("%Y-%m-%d %H:%M:%S")]]
                result = self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range='ZZ1:ZZ1',  # Usa una cella lontana per il test
                    valueInputOption='USER_ENTERED',
                    body={'values': test_data}
                ).execute()
                logger.info("✅ Scrittura riuscita")
                
                # Pulisce il test
                self.service.spreadsheets().values().clear(
                    spreadsheetId=self.spreadsheet_id,
                    range='ZZ1:ZZ1'
                ).execute()
                logger.info("✅ Pulizia test completata")
                
            except HttpError as e:
                logger.error(f"❌ Errore nella scrittura: {e}")
                if e.resp.status == 403:
                    logger.error("💡 Il service account non ha permessi di scrittura")
                return False
                
            logger.info("=" * 50)
            logger.info("🎉 TUTTI I TEST COMPLETATI CON SUCCESSO!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore generale nel test: {e}")
            return False
            
    def diagnose_error(self, error: Exception):
        """Diagnostica errori specifici"""
        logger.info("🔍 DIAGNOSI ERRORE:")
        
        if isinstance(error, HttpError):
            status = error.resp.status
            if status == 403:
                logger.error("❌ Errore 403 - Accesso negato")
                logger.error("💡 Soluzioni:")
                logger.error("   1. Condividi il foglio con l'email del service account")
                logger.error("   2. Verifica che il service account abbia i permessi giusti")
                logger.error("   3. Controlla che l'API Google Sheets sia abilitata")
            elif status == 404:
                logger.error("❌ Errore 404 - Foglio non trovato")
                logger.error("💡 Verifica l'ID del foglio Google Sheets")
            elif status == 401:
                logger.error("❌ Errore 401 - Credenziali non valide")
                logger.error("💡 Rigenera le credenziali del service account")
        else:
            logger.error(f"❌ Errore generico: {error}")

def main():
    """Funzione principale per test credenziali"""
    print("🔍 TEST CREDENZIALI GOOGLE SHEETS")
    print("=" * 50)
    
    # Ottieni credenziali
    credentials_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
    if not credentials_json:
        print("❌ Credenziali non trovate nelle variabili d'ambiente")
        print("💡 Imposta GOOGLE_SHEETS_CREDENTIALS")
        return False
    
    # Esegui test
    tester = CredentialsTest()
    success = tester.test_credentials(credentials_json)
    
    if success:
        print("\n✅ Test completato con successo!")
    else:
        print("\n❌ Test fallito!")
        
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 