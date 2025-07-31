#!/usr/bin/env python3
"""
Revenue Analysis Parallelo Ottimizzato - Entry Point
Sistema di web scraping parallelo con utenti finti per analisi ricavi competitor
"""

import sys
import argparse
import logging
import time
from datetime import datetime
from pathlib import Path

# Import moduli locali
from config import VESTIAIRE_PROFILES, OPTIMIZATION_CONFIG
from revenue_scraper import RevenueScraper
from revenue_sheets_updater import RevenueSheetsUpdater

# Configurazione logging
def setup_logging():
    """Configura il sistema di logging"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"revenue_analysis_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def test_users():
    """Test sistema utenti finti"""
    logger = logging.getLogger(__name__)
    logger.info("🧪 === TEST SISTEMA UTENTI FINTI ===")
    
    try:
        scraper = RevenueScraper()
        
        # Test con un profilo
        test_profile = "Vintage & Modern"
        profile_id = VESTIAIRE_PROFILES[test_profile]
        
        logger.info(f"🔍 Test utenti finti per {test_profile} (ID: {profile_id})")
        
        # Test navigazione base
        success = scraper._test_user_navigation(test_profile, profile_id)
        
        if success:
            logger.info("✅ Test utenti finti PASSATO")
            return True
        else:
            logger.error("❌ Test utenti finti FALLITO")
            return False
            
    except Exception as e:
        logger.error(f"❌ Errore test utenti finti: {e}")
        return False

def test_flagging():
    """Test algoritmo flagging articoli venduti"""
    logger = logging.getLogger(__name__)
    logger.info("🏷️ === TEST FLAGGING ARTICOLI VENDUTI ===")
    
    try:
        scraper = RevenueScraper()
        
        # Test con Vintage & Modern (37 vendite reali)
        test_profile = "Vintage & Modern"
        profile_id = VESTIAIRE_PROFILES[test_profile]
        
        logger.info(f"🔍 Test flagging per {test_profile} (ID: {profile_id})")
        
        # Test flagging
        sold_count = scraper._test_flagging_algorithm(test_profile, profile_id)
        
        if sold_count == 37:
            logger.info(f"✅ Test flagging PASSATO: {sold_count} vendite trovate")
            return True
        else:
            logger.warning(f"⚠️ Test flagging PARZIALE: {sold_count} vendite (attese: 37)")
            return False
            
    except Exception as e:
        logger.error(f"❌ Errore test flagging: {e}")
        return False

def test_prices():
    """Test estrazione prezzi di vendita finali"""
    logger = logging.getLogger(__name__)
    logger.info("💰 === TEST ESTRAZIONE PREZZI FINALI ===")
    
    try:
        scraper = RevenueScraper()
        
        # Test con un profilo
        test_profile = "Vintage & Modern"
        profile_id = VESTIAIRE_PROFILES[test_profile]
        
        logger.info(f"🔍 Test prezzi per {test_profile} (ID: {profile_id})")
        
        # Test estrazione prezzi
        prices = scraper._test_price_extraction(test_profile, profile_id)
        
        if prices:
            logger.info(f"✅ Test prezzi PASSATO: {len(prices)} prezzi estratti")
            logger.info(f"   Prezzi: {prices[:5]}...")  # Mostra primi 5
            return True
        else:
            logger.warning("⚠️ Test prezzi PARZIALE: nessun prezzo estratto")
            return False
            
    except Exception as e:
        logger.error(f"❌ Errore test prezzi: {e}")
        return False

def test_parallel():
    """Test sistema parallelo"""
    logger = logging.getLogger(__name__)
    logger.info("⚡ === TEST SISTEMA PARALLELO ===")
    
    try:
        scraper = RevenueScraper()
        
        # Test con 3 profili
        test_profiles = ["Vintage & Modern", "Rediscover", "Volodymyr"]
        
        logger.info(f"🔍 Test parallelo con {len(test_profiles)} profili")
        
        # Test sistema parallelo
        results = scraper._test_parallel_system(test_profiles)
        
        if results:
            logger.info(f"✅ Test parallelo PASSATO: {len(results)} profili processati")
            for profile, result in results.items():
                logger.info(f"   {profile}: {result}")
            return True
        else:
            logger.error("❌ Test parallelo FALLITO")
            return False
            
    except Exception as e:
        logger.error(f"❌ Errore test parallelo: {e}")
        return False

def test_sheets():
    """Test aggiornamento Google Sheets"""
    logger = logging.getLogger(__name__)
    logger.info("📊 === TEST GOOGLE SHEETS ===")
    
    try:
        sheets_updater = RevenueSheetsUpdater()
        
        # Test connessione
        success = sheets_updater._test_connection()
        
        if success:
            logger.info("✅ Test Google Sheets PASSATO")
            return True
        else:
            logger.error("❌ Test Google Sheets FALLITO")
            return False
            
    except Exception as e:
        logger.error(f"❌ Errore test Google Sheets: {e}")
        return False

def test_performance():
    """Test performance completo"""
    logger = logging.getLogger(__name__)
    logger.info("🚀 === TEST PERFORMANCE COMPLETO ===")
    
    try:
        scraper = RevenueScraper()
        
        # Test con tutti i profili
        start_time = time.time()
        
        results = scraper.scrape_all_profiles_revenue()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        logger.info(f"⏱️ Tempo totale: {total_time:.2f} secondi")
        logger.info(f"📊 Profili processati: {len(results)}")
        
        # Calcola metriche
        avg_time_per_profile = total_time / len(results) if results else 0
        total_revenue = sum(result.get('revenue', 0) for result in results.values())
        total_items = sum(result.get('items_sold', 0) for result in results.values())
        
        logger.info(f"📈 Metriche:")
        logger.info(f"   Tempo medio per profilo: {avg_time_per_profile:.2f}s")
        logger.info(f"   Ricavi totali: €{total_revenue:.2f}")
        logger.info(f"   Articoli venduti totali: {total_items}")
        
        # Verifica metriche PRD
        if avg_time_per_profile < 30:
            logger.info("✅ Metriche PRD RISPETTATE: tempo < 30s per profilo")
        else:
            logger.warning("⚠️ Metriche PRD NON RISPETTATE: tempo > 30s per profilo")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore test performance: {e}")
        return False

def main():
    """Funzione principale"""
    parser = argparse.ArgumentParser(description="Revenue Analysis Parallelo Ottimizzato")
    parser.add_argument("command", choices=[
        "test-users", "test-flagging", "test-prices", "test-parallel", 
        "test-sheets", "performance", "run"
    ], help="Comando da eseguire")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    logger.info("🚀 === REVENUE ANALYSIS PARALLELO OTTIMIZZATO ===")
    logger.info(f"📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🎯 Comando: {args.command}")
    
    # Esegui comando
    if args.command == "test-users":
        success = test_users()
    elif args.command == "test-flagging":
        success = test_flagging()
    elif args.command == "test-prices":
        success = test_prices()
    elif args.command == "test-parallel":
        success = test_parallel()
    elif args.command == "test-sheets":
        success = test_sheets()
    elif args.command == "performance":
        success = test_performance()
    elif args.command == "run":
        # Esecuzione completa
        logger.info("🏃 Esecuzione completa del sistema...")
        scraper = RevenueScraper()
        results = scraper.scrape_all_profiles_revenue()
        
        # Aggiorna Google Sheets
        sheets_updater = RevenueSheetsUpdater()
        sheets_updater.update_revenue_sheets(results)
        
        success = True
    
    # Risultato finale
    if success:
        logger.info("✅ Comando completato con successo")
        sys.exit(0)
    else:
        logger.error("❌ Comando fallito")
        sys.exit(1)

if __name__ == "__main__":
    main() 