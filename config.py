"""
Configurazione Vestiaire Monitor
File di configurazione per le impostazioni del monitoraggio
Ultimo aggiornamento: 2024-12-19 16:45 CET - FORCE REFRESH
"""

import os
from typing import Dict, List

# Configurazione Google Sheets
GOOGLE_SHEETS_CONFIG = {
    "spreadsheet_id": "1sWmvdbEgzLCyaNk5XRDHOFTA5KY1RGeMBIqouXvPJ34",
    "main_sheet": "riepilogo",
    "credentials_files": [
        "vestiaire-monitor-ba3e8b6417eb.json",
        "credentials.json",
        "google-sheets-credentials.json"
    ]
}

# Configurazione profili Vestiaire
VESTIAIRE_PROFILES = {
    "Rediscover": "2039815",
    "Volodymyr": "5924329", 
    "stephanie": "9168643",
    "Mark": "13442939",
    "A Retro Tale": "5537180",
    "Lapsa": "11345596",
    "Clara": "27862876",
    "Baggy Vintage": "18106856",
    "Vintageandkickz": "19199976",
    "Vintage & Modern": "29517320",
    "Hugo": "21940019",
    "Plamexs": "8642167",
    "The Brand Collector": "4085582"
}

# Configurazione performance e tempi
PERFORMANCE_CONFIG = {
    # Tempi di attesa (in secondi)
    "page_load_wait": 5,        # Tempo di attesa per il caricamento della pagina
    "between_profiles_wait": 3,  # Tempo di attesa tra profili
    "request_timeout": 30,       # Timeout per le richieste HTTP
    
    # Configurazione Chrome
    "chrome_options": {
        "headless": True,
        "disable_images": False,    # Disabilita il caricamento delle immagini per velocizzare
        "disable_css": False,       # Disabilita CSS per velocizzare
        "window_size": "1920,1080"
    },
    
    # Soglie di performance
    "performance_thresholds": {
        "excellent_profile_time": 8,  # Sotto 8s = eccellente
        "good_profile_time": 12,      # Sotto 12s = buona
        "slow_connection_threshold": 7,  # Sopra 7s caricamento = lenta
        "min_efficiency": 50          # Efficienza minima accettabile (%)
    },
    
    # Retry e resilienza
    "retry_config": {
        "max_retries": 3,           # Numero massimo di tentativi per profilo
        "retry_delay": 2,           # Attesa tra i tentativi
        "timeout_retry": True       # Ritenta su timeout
    }
}

# Configurazione logging
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "performance_logging": True,    # Abilita logging dettagliato delle performance
    "save_performance_logs": True,  # Salva logs delle performance su file
    "log_file": "vestiaire_performance.log"
}

# Configurazione modalità test
TEST_CONFIG = {
    "test_profiles": ["Rediscover", "Volodymyr"],  # Profili da usare per i test rapidi
    "benchmark_runs": 3,            # Numero di esecuzioni per benchmark
    "performance_report_file": "performance_report.json"
}

# Configurazione avanzata per ottimizzazioni
OPTIMIZATION_CONFIG = {
    "parallel_scraping": False,     # Scraping parallelo (sperimentale)
    "max_parallel_workers": 3,      # Numero massimo di worker paralleli
    "cache_driver": True,           # Cache del driver Chrome tra esecuzioni
    "smart_wait": True,             # Attesa intelligente basata sul caricamento
    "adaptive_delays": True,        # Adatta i tempi di attesa in base alle performance
}

def get_config_summary() -> Dict:
    """Restituisce un riassunto delle configurazioni attuali"""
    return {
        "profiles_count": len(VESTIAIRE_PROFILES),
        "page_load_wait": PERFORMANCE_CONFIG["page_load_wait"],
        "between_profiles_wait": PERFORMANCE_CONFIG["between_profiles_wait"],
        "estimated_total_time": len(VESTIAIRE_PROFILES) * (
            PERFORMANCE_CONFIG["page_load_wait"] + 
            PERFORMANCE_CONFIG["between_profiles_wait"] + 3  # +3 per processing
        ),
        "performance_thresholds": PERFORMANCE_CONFIG["performance_thresholds"],
        "chrome_headless": PERFORMANCE_CONFIG["chrome_options"]["headless"],
        "optimization_enabled": any(OPTIMIZATION_CONFIG.values())
    }

def update_performance_config(new_config: Dict):
    """Aggiorna la configurazione delle performance"""
    global PERFORMANCE_CONFIG
    PERFORMANCE_CONFIG.update(new_config)

def get_test_profiles() -> Dict:
    """Restituisce solo i profili configurati per i test"""
    return {name: VESTIAIRE_PROFILES[name] for name in TEST_CONFIG["test_profiles"] if name in VESTIAIRE_PROFILES}

def get_chrome_options() -> List[str]:
    """Restituisce le opzioni Chrome formattate"""
    options = []
    config = PERFORMANCE_CONFIG["chrome_options"]
    
    if config["headless"]:
        options.append("--headless")
    
    options.extend([
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        f"--window-size={config['window_size']}",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ])
    
    if config["disable_images"]:
        options.append("--blink-settings=imagesEnabled=false")
    
    if config["disable_css"]:
        options.append("--disable-web-security")
    
    return options

# Configurazione per modalità debug
DEBUG_CONFIG = {
    "debug_mode": False,
    "verbose_logging": False,
    "save_html_snapshots": False,
    "screenshot_on_error": False,
    "debug_first_profile_only": False
}

def print_config_info():
    """Stampa informazioni sulla configurazione attuale"""
    summary = get_config_summary()
    
    print("🔧 CONFIGURAZIONE VESTIAIRE MONITOR")
    print("="*50)
    print(f"Profili da scrapare: {summary['profiles_count']}")
    print(f"Tempo attesa pagina: {summary['page_load_wait']}s")
    print(f"Tempo tra profili: {summary['between_profiles_wait']}s")
    print(f"Tempo stimato totale: {summary['estimated_total_time']}s (~{summary['estimated_total_time']//60:.0f}m)")
    print(f"Chrome headless: {'Sì' if summary['chrome_headless'] else 'No'}")
    print(f"Ottimizzazioni attive: {'Sì' if summary['optimization_enabled'] else 'No'}")
    print("="*50)

if __name__ == "__main__":
    print_config_info() 