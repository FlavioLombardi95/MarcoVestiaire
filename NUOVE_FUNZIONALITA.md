# Nuove Funzionalità - Vestiaire Monitor

## 🆕 Funzionalità Aggiunte

### 1. Seconda Colonna nelle Tab Mensili

**Descrizione**: Ogni tab mensile ora include una seconda colonna che mostra la somma totale delle "diff vendite" del mese per ogni profilo.

**Struttura aggiornata**:
- **Colonna A**: Profilo
- **Colonna B**: Diff Vendite [Mese] (NUOVA)
- **Colonna C**: URL
- **Colonne D+**: Dati giornalieri (articoli, vendite, diff stock, diff vendite)

**Funzionalità**:
- Calcolo automatico della somma delle diff vendite giornaliere
- Aggiornamento automatico ad ogni esecuzione del monitoraggio
- Gestione di celle vuote (considerate come 0)

### 2. Tab Overview

**Descrizione**: Nuova tab che fornisce una vista panoramica dei totali mensili delle diff vendite per tutti i profili.

**Struttura**:
- **Righe**: Profili (13 profili configurati)
- **Colonne**: Mesi (solo tab esistenti)
- **Valori**: Totali mensili delle diff vendite

**Funzionalità**:
- Creazione automatica della tab se non esiste
- Aggiornamento automatico ad ogni esecuzione
- Lettura dati da tutte le tab mensili esistenti
- Formattazione automatica con colori alternati
- Ordinamento cronologico dei mesi

## 🔧 Comandi di Test

Sono stati aggiunti nuovi comandi per testare le funzionalità:

```bash
# Test della tab Overview
python main.py test-overview

# Test della colonna diff vendite mensili
python main.py test-diff-vendite
```

## 📊 Esempio di Output

### Tab Mensile (es. july)
```
| Profilo      | Diff Vendite July | URL                    | 1 july | ... |
|--------------|-------------------|------------------------|--------|-----|
| Rediscover   | 45               | https://...           | 592    | ... |
| Volodymyr    | 12               | https://...           | 0      | ... |
| ...          | ...              | ...                   | ...    | ... |
```

### Tab Overview
```
| Profilo      | July | August | September | ... |
|--------------|------|--------|-----------|-----|
| Rediscover   | 45   | 23     | 67        | ... |
| Volodymyr    | 12   | 8      | 15        | ... |
| ...          | ...  | ...    | ...       | ... |
```

## 🔄 Integrazione Automatica

Le nuove funzionalità sono completamente integrate nel flusso esistente:

1. **Esecuzione normale**: `python main.py`
   - Aggiorna la tab mensile con i dati del giorno
   - Calcola e aggiorna la seconda colonna con i totali mensili
   - Aggiorna la tab Overview

2. **Nessuna modifica alla struttura esistente**
   - Tutte le funzioni esistenti continuano a funzionare
   - I dati esistenti non vengono modificati
   - Solo aggiunta di nuove colonne e tab

## 🎯 Gestione Errori

- **Celle vuote**: Considerate come 0 nel calcolo
- **Tab inesistenti**: Ignorate nella tab Overview
- **Dati mancanti**: Gestiti con valori di default
- **Errori di calcolo**: Loggati ma non bloccano l'esecuzione

## 📝 Note Tecniche

- **Compatibilità**: Funziona con tutte le tab mensili esistenti
- **Performance**: Calcoli ottimizzati per non rallentare l'esecuzione
- **Scalabilità**: Supporta automaticamente nuovi mesi e profili
- **Formattazione**: Applicata automaticamente alle nuove sezioni 