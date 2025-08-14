#!/usr/bin/env python3
"""
Test completo per tutti i profili del Revenue Scraper
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

def test_all_profiles():
    """Test dello scraping per tutti i profili"""
    logger.info("=== TEST COMPLETO REVENUE SCRAPING ===")
    
    try:
        # Inizializza scraper
        scraper = RevenueScraper(profiles=VESTIAIRE_PROFILES)
        
        # Esegui scraping per tutti i profili
        results = scraper.scrape_all_profiles_revenue()
        
        # Analizza risultati
        total_revenue = 0
        total_items = 0
        successful_profiles = 0
        
        logger.info("\n=== RISULTATI TEST ===")
        
        for result in results:
            if result['success']:
                successful_profiles += 1
                profile_name = result['name']
                sold_count = result['sold_items_count']
                revenue = result['total_revenue']
                prices_count = len(result['sold_items_prices'])
                
                total_revenue += revenue
                total_items += sold_count
                
                logger.info(f"{profile_name}: {sold_count} articoli venduti, €{revenue:.2f} ricavi ({prices_count} prezzi estratti)")
                
                # Verifica speciale per Vintage & Modern
                if profile_name == "Vintage & Modern":
                    if sold_count == 37:
                        logger.info("🎯 SUCCESSO: Vintage & Modern ha le 37 vendite corrette!")
                    else:
                        logger.warning(f"⚠️ ATTENZIONE: Vintage & Modern ha {sold_count} vendite invece di 37")
            else:
                logger.error(f"❌ {result['name']}: {result.get('error', 'Errore sconosciuto')}")
        
        logger.info(f"\nTOTALI: {successful_profiles}/{len(results)} profili validi")
        logger.info(f"TOTALI: {total_items} articoli venduti, €{total_revenue:.2f} ricavi totali")
        
        # Statistiche
        if successful_profiles > 0:
            avg_revenue = total_revenue / successful_profiles
            avg_items = total_items / successful_profiles
            logger.info(f"MEDIA: {avg_items:.1f} articoli per profilo, €{avg_revenue:.2f} ricavi per profilo")
            
    except Exception as e:
        logger.error(f"Errore test completo: {e}")

if __name__ == "__main__":
    test_all_profiles() 