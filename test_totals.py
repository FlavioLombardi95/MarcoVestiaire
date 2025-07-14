#!/usr/bin/env python3
"""
Test semplice per verificare i calcoli dei totali nelle Google Sheets
"""

import os
import sys
import traceback

# Aggiungi il percorso src al PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from sheets_updater import GoogleSheetsUpdater

def test_totals():
    """Test dei calcoli dei totali nelle Google Sheets"""
    try:
        print("🔍 TEST TOTALI GOOGLE SHEETS")
        print("=" * 50)
        
        # Configura le credenziali
        credentials_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
        if not credentials_json:
            print("❌ ERRORE: Credenziali Google Sheets non trovate")
            print("💡 Assicurati di aver impostato la variabile d'ambiente GOOGLE_SHEETS_CREDENTIALS")
            return False
            
        # Inizializza l'updater
        updater = GoogleSheetsUpdater(credentials_json)
        
        # Leggi i dati attuali del foglio luglio
        month_name = "july"
        year = 2024
        
        print(f"📖 Lettura dati da {month_name} {year}...")
        
        result = updater.service.spreadsheets().values().get(
            spreadsheetId=updater.spreadsheet_id,
            range=f"{month_name}!A:ZZ"
        ).execute()
        
        values = result.get('values', [])
        if not values:
            print(f"❌ ERRORE: Tab {month_name} vuota!")
            return False
            
        header = values[0]
        print(f"📊 Header: {header}")
        print(f"📊 Numero righe: {len(values)}")
        
        # Analizza ogni colonna per i totali
        print("\n🔢 ANALISI COLONNE E TOTALI:")
        print("-" * 40)
        
        for col_idx in range(2, min(len(header), 10)):  # Limita a 10 colonne per brevità
            col_name = header[col_idx] if col_idx < len(header) else f"Col_{col_idx}"
            print(f"\n📋 Colonna {col_idx}: {col_name}")
            
            col_sum = 0
            valid_values = []
            invalid_values = []
            
            # Calcola somma escludendo header e riga totali
            for row_idx in range(1, len(values)):
                row = values[row_idx]
                if row and row[0] == "Totali":
                    continue  # Salta la riga totali
                    
                if col_idx < len(row) and row[col_idx]:
                    cell_value = row[col_idx]
                    try:
                        # Usa la stessa logica del codice aggiornato
                        clean_val = str(cell_value).replace("'", "").replace(" ", "").strip()
                        numeric_val = int(clean_val) if clean_val else 0
                        col_sum += numeric_val
                        valid_values.append(f"R{row_idx+1}: {numeric_val}")
                    except (ValueError, TypeError):
                        invalid_values.append(f"R{row_idx+1}: '{cell_value}' (non numerico)")
                        
            print(f"✅ Somma calcolata: {col_sum}")
            print(f"📊 Valori validi: {len(valid_values)}")
            if len(valid_values) <= 3:
                for val in valid_values:
                    print(f"   - {val}")
            else:
                print(f"   - Prime 2: {valid_values[:2]}")
                print(f"   - Ultima: {valid_values[-1]}")
                    
            if invalid_values:
                print(f"⚠️  Valori non numerici: {len(invalid_values)}")
                for val in invalid_values[:2]:  # Mostra solo i primi 2
                    print(f"   - {val}")
                    
        # Trova la riga dei totali attuale
        print("\n🎯 RIGA TOTALI ATTUALE:")
        print("-" * 30)
        
        totals_row = None
        totals_row_idx = None
        
        for row_idx, row in enumerate(values):
            if row and row[0] == "Totali":
                totals_row = row
                totals_row_idx = row_idx
                break
                
        if totals_row:
            print(f"📍 Riga totali trovata alla posizione {totals_row_idx + 1}")
            print(f"📋 Contenuto (prime 10 colonne): {totals_row[:10]}")
            
            # Confronta con calcolo corretto
            print("\n🔍 CONFRONTO CALCOLO CORRETTO:")
            print("-" * 35)
            
            problemi_trovati = 0
            
            for col_idx in range(2, min(len(header), len(totals_row), 10)):
                col_name = header[col_idx] if col_idx < len(header) else f"Col_{col_idx}"
                
                # Calcola somma corretta
                correct_sum = 0
                for row_idx in range(1, len(values)):
                    row = values[row_idx]
                    if row and row[0] == "Totali":
                        continue
                    if col_idx < len(row) and row[col_idx]:
                        try:
                            clean_val = str(row[col_idx]).replace("'", "").replace(" ", "").strip()
                            correct_sum += int(clean_val) if clean_val else 0
                        except (ValueError, TypeError):
                            pass
                            
                current_total = totals_row[col_idx] if col_idx < len(totals_row) else ""
                
                if str(correct_sum) == str(current_total):
                    print(f"✅ {col_name}: {current_total} (corretto)")
                else:
                    print(f"❌ {col_name}: attuale='{current_total}', corretto={correct_sum}")
                    problemi_trovati += 1
                    
            print(f"\n📊 RIEPILOGO: {problemi_trovati} problemi trovati")
                    
        else:
            print("⚠️  Nessuna riga totali trovata!")
            
        print("\n" + "=" * 50)
        print("🔍 Test totali completato")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore nel test totali: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_totals()
    sys.exit(0 if success else 1) 