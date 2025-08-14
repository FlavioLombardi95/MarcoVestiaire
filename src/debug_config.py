#!/usr/bin/env python3
"""
Configurazione avanzata per debug e logging
"""

import os
from datetime import datetime

# Configurazione debug
DEBUG_CONFIG = {
    'enable_detailed_logging': True,
    'save_debug_data': True,
    'capture_screenshots': True,
    'performance_monitoring': True,
    'validate_data_quality': True,
    'compare_with_previous': True,
    'log_network_requests': True,
    'track_memory_usage': False,
    'enable_profiling': False
}

# Configurazione logging
LOG_CONFIG = {
    'log_level': 'INFO',
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'max_log_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5,
    'console_output': True,
    'file_output': True,
    'github_actions_output': True
}

# Soglie di performance per alerting
PERFORMANCE_THRESHOLDS = {
    'max_profile_time': 15.0,  # secondi
    'max_total_time': 300.0,   # secondi (5 minuti)
    'min_success_rate': 0.8,   # 80%
    'max_error_rate': 0.2,     # 20%
    'network_timeout': 30.0    # secondi
}

# Configurazione per validazione dati
DATA_VALIDATION = {
    'min_articles_per_profile': 0,
    'max_articles_per_profile': 50000,
    'min_sales_per_profile': 0,
    'max_sales_per_profile': 100000,
    'detect_static_data': True,
    'static_data_threshold': 5,  # numero di esecuzioni consecutive con stessi dati
    'validate_totals': True,
    'check_differences': True
}

# Paths per file di debug
DEBUG_PATHS = {
    'logs_dir': 'logs',
    'debug_data_dir': 'logs/debug_data',
    'screenshots_dir': 'logs/screenshots',
    'performance_dir': 'logs/performance',
    'validation_dir': 'logs/validation'
}

def get_debug_filename(prefix: str, extension: str = 'log') -> str:
    """Genera un nome file di debug con timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"

def ensure_debug_dirs():
    """Crea le directory necessarie per il debug"""
    for dir_path in DEBUG_PATHS.values():
        os.makedirs(dir_path, exist_ok=True)

def is_github_actions() -> bool:
    """Controlla se stiamo eseguendo in GitHub Actions"""
    return os.environ.get('GITHUB_ACTIONS') == 'true'

def get_log_level():
    """Ottiene il livello di logging basato sull'ambiente"""
    if is_github_actions():
        return 'INFO'
    return os.environ.get('LOG_LEVEL', LOG_CONFIG['log_level'])

def should_save_debug_data() -> bool:
    """Determina se salvare i dati di debug"""
    return DEBUG_CONFIG['save_debug_data'] and (
        is_github_actions() or 
        os.environ.get('SAVE_DEBUG_DATA', 'true').lower() == 'true'
    )

# Messaggi di debug formattati
DEBUG_MESSAGES = {
    'start': "🚀 AVVIO VESTIAIRE MONITOR",
    'credentials_ok': "✅ Credenziali Google Sheets trovate",
    'credentials_missing': "❌ Credenziali Google Sheets non trovate",
    'scraping_start': "📡 Avvio scraping dei profili...",
    'scraping_complete': "✅ Scraping completato",
    'scraping_failed': "❌ Scraping fallito",
    'sheets_update_start': "📝 Aggiornamento Google Sheets...",
    'sheets_update_complete': "✅ Aggiornamento Google Sheets completato",
    'sheets_update_failed': "❌ Errore nell'aggiornamento Google Sheets",
    'success': "✅ VESTIAIRE MONITOR COMPLETATO CON SUCCESSO",
    'failure': "❌ VESTIAIRE MONITOR FALLITO",
    'debug_data_saved': "📝 Dati di debug salvati",
    'performance_analysis': "📊 Analisi performance completata",
    'data_validation': "🔍 Validazione dati completata",
    'totals_check': "🧮 Controllo totali completato"
}

def get_debug_message(key: str, *args) -> str:
    """Ottiene un messaggio di debug formattato"""
    message = DEBUG_MESSAGES.get(key, f"Debug: {key}")
    if args:
        return message + f" ({', '.join(map(str, args))})"
    return message 