#!/usr/bin/env python3
"""
Test script per il Revenue Scraper
"""

import sys
import os
import logging
from datetime import datetime

# Aggiungi il percorso del progetto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from revenue_scraper import RevenueScraper
from config import VESTIAIRE_PROFILES

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_revenue_scraping():
    """Test dello scraping dei ricavi"""
    logger.info("=== TEST REVENUE SCRAPING ===")
    
    try:
        # Inizializza scraper
        scraper = RevenueScraper(profiles=VESTIAIRE_PROFILES)
        
        # Test specifico per Vintage & Modern
        profile_name = "Vintage & Modern"
        profile_id = VESTIAIRE_PROFILES[profile_name]
        
        logger.info(f"🔍 Test specifico per {profile_name} (ID: {profile_id})")
        
        # Esegui scraping
        result = scraper.scrape_profile_revenue(profile_name, profile_id)
        
        if result['success']:
            logger.info(f"✅ {profile_name}: {result['sold_items_count']} articoli venduti, €{result['total_revenue']:.2f} ricavi (⏱️ {result['performance']['total_time']:.2f}s)")
            
            # Verifica se ha trovato le 37 vendite reali
            if result['sold_items_count'] == 37:
                logger.info("🎯 SUCCESSO: Trovate le 37 vendite reali!")
            else:
                logger.warning(f"⚠️ ATTENZIONE: Trovate {result['sold_items_count']} vendite invece delle 37 attese")
                
        else:
            logger.error(f"❌ Errore per {profile_name}: {result.get('error', 'Errore sconosciuto')}")
            
    except Exception as e:
        logger.error(f"Errore test: {e}")

if __name__ == "__main__":
    test_revenue_scraping() 