#!/usr/bin/env python3
"""
Test per analizzare la struttura delle colonne del mese di luglio
"""

import calendar
from datetime import datetime

def analyze_july_structure():
    """Analizza la struttura delle colonne per il mese di luglio"""
    
    # Simula la struttura attesa
    print("=== ANALISI STRUTTURA COLONNE LUGLIO ===")
    
    # Per luglio 2024 (31 giorni)
    year = 2024
    month = 7  # luglio
    month_name = "july"
    days_in_month = calendar.monthrange(year, month)[1]
    
    print(f"Mese: {month_name} {year}")
    print(f"Giorni nel mese: {days_in_month}")
    
    # Struttura attesa dal codice
    print("\n=== STRUTTURA ATTESA DAL CODICE ===")
    print("Colonna A: Profilo")
    print("Colonna B: Diff Vendite July") 
    print("Colonna C: URL")
    print("Colonna D+: Dati giornalieri (4 colonne per giorno)")
    
    # Calcolo colonne per il 31 luglio
    base_col_31 = 3 + (31-1)*4  # 3 + 30*4 = 123
    articoli_col_31 = base_col_31
    vendite_col_31 = base_col_31 + 1
    
    print(f"\n=== COLONNE PER IL 31 LUGLIO ===")
    print(f"Base colonna: {base_col_31}")
    print(f"Articoli (31 luglio): colonna {articoli_col_31}")
    print(f"Vendite (31 luglio): colonna {vendite_col_31}")
    
    # Verifica se le colonne sono ragionevoli
    if base_col_31 > 100:
        print(f"\n⚠️  ATTENZIONE: La colonna {base_col_31} sembra troppo alta!")
        print("   Questo potrebbe indicare un problema nel calcolo.")
    
    # Mostra alcune colonne di esempio
    print(f"\n=== ESEMPI DI COLONNE ===")
    for day in [1, 15, 31]:
        base_col = 3 + (day-1)*4
        print(f"Giorno {day}: articoli=colonna {base_col}, vendite=colonna {base_col+1}")
    
    # Possibili problemi
    print(f"\n=== POSSIBILI PROBLEMI ===")
    print("1. La tab 'july' potrebbe non esistere")
    print("2. La struttura delle colonne potrebbe essere diversa")
    print("3. I dati del 31 luglio potrebbero non essere presenti")
    print("4. Il calcolo delle colonne potrebbe essere errato")
    
    # Suggerimenti
    print(f"\n=== SUGGERIMENTI ===")
    print("1. Verificare che la tab 'july' esista")
    print("2. Controllare la struttura delle intestazioni")
    print("3. Verificare che i dati del 31 luglio siano presenti")
    print("4. Controllare se il calcolo delle colonne è corretto")

def test_column_calculation():
    """Test del calcolo delle colonne"""
    print("\n=== TEST CALCOLO COLONNE ===")
    
    # Test per diversi mesi
    test_cases = [
        (2024, 7, 31),   # luglio 2024, 31 giorni
        (2024, 8, 31),   # agosto 2024, 31 giorni
        (2025, 1, 31),   # gennaio 2025, 31 giorni
    ]
    
    for year, month, days in test_cases:
        month_name = calendar.month_name[month].lower()
        print(f"\n{month_name.capitalize()} {year} ({days} giorni):")
        
        for day in [1, days//2, days]:
            base_col = 3 + (day-1)*4
            print(f"  Giorno {day}: colonne {base_col}-{base_col+3}")

if __name__ == "__main__":
    analyze_july_structure()
    test_column_calculation() 