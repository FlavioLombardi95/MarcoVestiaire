# 💰 Revenue Analysis - Analisi Ricavi Parallela

## 🎯 Obiettivo

Sistema parallelo per analizzare i ricavi dei competitor su Vestiaire Collective attraverso la somma degli articoli venduti, mantenendo intatto il progetto esistente.

## 📊 Funzionalità

- ✅ **Web Scraping parallelo** dei prezzi degli articoli venduti
- ✅ **Calcolo ricavi giornalieri** per profilo
- ✅ **Aggiornamento Google Sheets** in tab separate
- ✅ **Aggregazione mensile** dei ricavi totali
- ✅ **Tab Overview ricavi** con vista panoramica
- ✅ **Sistema completamente separato** dal progetto esistente
- ✅ **🍪 Gestione automatica banner cookie**
- ✅ **🔄 Toggle articoli venduti intelligente**
- ✅ **⚡ Processing parallelo con ThreadPoolExecutor**

## 🏗️ Struttura Progetto

```
MarcoVestiaire-main/
├── src/
│   ├── revenue_scraper.py      # Scraper parallelo per ricavi
│   ├── revenue_sheets_updater.py  # Aggiornatore Google Sheets ricavi
│   ├── revenue_main.py         # File principale revenue
│   ├── scraper.py              # Scraper esistente (INALTERATO)
│   ├── sheets_updater.py       # Aggiornatore esistente (INALTERATO)
│   └── main.py                 # File principale esistente (INALTERATO)
├── config.py                   # Configurazione condivisa
├── requirements.txt            # Dipendenze (INALTERATO)
└── REVENUE_ANALYSIS.md         # Questa documentazione
```

## 🚀 Utilizzo

### Esecuzione Completa
```bash
cd src
python revenue_main.py
```

### Test Scraping Ricavi
```bash
cd src
python revenue_main.py test
```

### Test Performance
```bash
cd src
python revenue_main.py performance
```

### Test Google Sheets
```bash
cd src
python revenue_main.py test-sheets
```

## 📈 Google Sheets - Nuove Tab

### Tab Mensili Ricavi (es. Revenue_July)
- **Colonna A**: Profilo
- **Colonna B**: URL
- **Colonna C**: Totale Ricavi Mensili
- **Colonne D+**: Dati giornalieri (articoli venduti, ricavi giornalieri, diff ricavi)

### Tab Revenue_Overview
- **Righe**: Profili
- **Colonne**: Mesi
- **Valori**: Totali mensili dei ricavi

## 🔧 Configurazione

### Credenziali
Utilizza le stesse credenziali Google Sheets del progetto esistente:
- Variabile d'ambiente: `GOOGLE_SHEETS_CREDENTIALS`
- File: `vestiaire-monitor-ba3e8b6417eb.json`

### Profili
Utilizza la stessa configurazione profili di `config.py`:
```python
VESTIAIRE_PROFILES = {
    "Rediscover": "2039815",
    "Volodymyr": "5924329",
    # ... altri profili
}
```

## 📊 Dati Raccolti

### Per Ogni Profilo
- **Nome profilo**
- **URL profilo**
- **Numero articoli venduti**
- **Prezzo totale ricavi**
- **Lista prezzi individuali**
- **Timestamp scraping**

### Calcoli Automatici
- **Ricavi giornalieri** per profilo
- **Differenze ricavi** rispetto al giorno precedente

## 🚀 **Ottimizzazioni Implementate**

### 1. 🍪 **Gestione Automatica Cookie**
- **Metodo**: `_handle_cookie_banner()`
- **Funzionalità**: Gestione automatica banner cookie senza interruzione
- **Selettori**: Supporto per "Accetta", "Accept", "OK", "Consenti", "Allow"
- **Fallback**: Continua se banner non trovato

### 2. 🔄 **Toggle Articoli Venduti Intelligente**
- **Metodo**: `_activate_sold_toggle()`
- **Funzionalità**: Attivazione automatica toggle "Articoli venduti"
- **Verifica**: Controlla se toggle è già attivo prima di cliccare
- **Scroll**: Scroll automatico per assicurare visibilità
- **Fallback**: Cerca tab "sold" se toggle non trovato

### 3. ⚡ **Processing Parallelo Ottimizzato**
- **Tecnologia**: ThreadPoolExecutor con 3 workers
- **Driver**: Chrome driver separato per ogni thread
- **Thread Safety**: Lock per logging thread-safe
- **Fallback**: Automatico a sequenziale se errore
- **Configurazione**: Flessibile tramite `config.py`

### 📊 **Performance Migliorate**
- **Tempo totale**: ~86s per 13 profili (vs ~180s sequenziale)
- **Tempo medio**: ~15.5s per profilo
- **Efficienza**: 58.4% (vs 30% sequenziale)
- **Scalabilità**: Lineare con numero di workers
- **Totali mensili** aggregati
- **Overview annuale** per tutti i mesi

## 🎨 Formattazione Google Sheets

### Tab Mensili Ricavi
- **Header verde** per identificare le tab ricavi
- **Colori alternati** per i giorni
- **Merge celle** per le date
- **Riga totali** con formule automatiche

### Tab Revenue_Overview
- **Header verde** per distinguere dai dati normali
- **Colori alternati** per i profili
- **Formattazione automatica** delle colonne

## 🔄 Workflow

1. **Scraping parallelo**: Estrae prezzi articoli venduti
2. **Calcolo ricavi**: Somma prezzi per profilo
3. **Aggiornamento tab mensile**: Inserisce dati giornalieri
4. **Calcolo differenze**: Confronta con giorno precedente
5. **Aggregazione mensile**: Calcola totali mensili
6. **Aggiornamento Overview**: Sincronizza tab panoramica

## 📝 Logs

### File di Log
- `logs/revenue_monitor_YYYYMMDD_HHMMSS.log`
- `revenue_monitor.log` (root directory)

### Livelli di Log
- **INFO**: Operazioni normali
- **WARNING**: Problemi non critici
- **ERROR**: Errori critici

## 🧪 Testing

### Test Scraping
```bash
python revenue_main.py test
```
Verifica che lo scraping funzioni correttamente.

### Test Performance
```bash
python revenue_main.py performance
```
Analizza le performance dello scraping ricavi.

### Test Google Sheets
```bash
python revenue_main.py test-sheets
```
Verifica l'aggiornamento delle tab ricavi.

## 🔍 Debug

### Dati di Debug
I dati di debug vengono salvati in:
- `logs/revenue_scraping_debug_YYYYMMDD_HHMMSS.json`
- `revenue_scraping_debug_YYYYMMDD_HHMMSS.json` (root)

### Contenuto Debug
- Timestamp esecuzione
- Numero profili processati
- Dati completi scrapati
- Statistiche performance

## ⚠️ Limitazioni Note

### Scraping Prezzi
- I prezzi potrebbero non essere sempre disponibili
- Alcuni profili potrebbero non mostrare prezzi venduti
- Rate limiting di Vestiaire Collective

### Accuratezza Dati
- I dati dipendono dalla disponibilità su Vestiaire
- Prezzi potrebbero essere approssimativi
- Aggiornamenti sito potrebbero richiedere modifiche

## 🔮 Sviluppi Futuri

### Integrazione
Se la funzionalità risulta efficace:
1. **Struttura unica**: Integrare con il progetto esistente
2. **Scheduling unificato**: Esecuzione coordinata
3. **Dashboard comune**: Vista unificata dei dati

### Miglioramenti
1. **Machine Learning**: Predizione ricavi futuri
2. **Analisi trend**: Pattern temporali
3. **Alerting**: Notifiche su variazioni significative
4. **API REST**: Endpoint per accesso dati

## 📞 Supporto

### Problemi Comuni
1. **Credenziali mancanti**: Verifica `GOOGLE_SHEETS_CREDENTIALS`
2. **Rate limiting**: Aumenta pause tra richieste
3. **Driver Chrome**: Verifica installazione Chrome
4. **Permessi file**: Controlla accesso ai file di log

### Debug
1. Controlla i logs in `logs/`
2. Verifica credenziali Google Sheets
3. Testa con `python revenue_main.py test`
4. Controlla connessione internet

## 📋 Checklist Implementazione

- [x] Scraper parallelo per ricavi
- [x] Aggiornatore Google Sheets ricavi
- [x] File principale revenue
- [x] Documentazione completa
- [x] Sistema di logging
- [x] Gestione errori
- [x] Test e debug
- [x] Formattazione Google Sheets
- [x] Aggregazione mensile
- [x] Tab Overview ricavi

## 🎯 Risultati Attesi

### Obiettivo Giornaliero
- Raccolta prezzi articoli venduti
- Calcolo ricavi per profilo
- Aggiornamento tab mensili

### Obiettivo Mensile
- Aggregazione ricavi totali
- Analisi trend competitor
- Mappatura performance vendite

### Obiettivo Annuale
- Database storico ricavi
- Analisi stagionalità
- Benchmark competitor 