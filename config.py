"""
Configurazione per Vestiaire Monitor
File di configurazione per credenziali e impostazioni
"""

import os
from typing import Dict, Any

# Configurazione Google Sheets
GOOGLE_SHEETS_CONFIG = {
    "spreadsheet_id": "1sWmvdbEgzLCyaNk5XRDHOFTA5KY1RGeMBIqouXvPJ34",
    "main_sheet": "Foglio1",
    "summary_sheet": "Riepilogo"
}

# Configurazione profili Vestiaire
VESTIAIRE_PROFILES = {
    "Rediscover": "2039815",
    "Volodymyr": "5924329", 
    "stephanie": "9168643",
    "Mark": "13442939",
    "A Retro Tale": "5537180",
    "Lapsa": "11345596",
    "Bag": "3770739",
    "Clara": "27862876",
    "Baggy Vintage": "18106856",
    "Vintageandkickz": "19199976",
    "Vintage & Modern": "29517320"
}

# Configurazione scraping
SCRAPING_CONFIG = {
    "delay_between_requests": 3,  # secondi
    "page_load_timeout": 10,      # secondi
    "max_retries": 3,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Configurazione logging
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "vestiaire_monitor.log"
}

def get_credentials() -> Dict[str, Any]:
    """Carica le credenziali Google Sheets"""
    credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
    if credentials_json:
        import json
        return json.loads(credentials_json)
    return {}

def get_config() -> Dict[str, Any]:
    """Restituisce la configurazione completa"""
    return {
        "google_sheets": GOOGLE_SHEETS_CONFIG,
        "vestiaire_profiles": VESTIAIRE_PROFILES,
        "scraping": SCRAPING_CONFIG,
        "logging": LOGGING_CONFIG,
        "credentials": get_credentials()
    } 