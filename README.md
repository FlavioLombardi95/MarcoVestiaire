# Vestiaire Monitor - Automazione Google Sheets

Sistema di automazione per monitorare i profili Vendors su Vestiaire Collective e aggiornare automaticamente un Google Sheet due volte al giorno.

## 🎯 Obiettivo

Monitorare automaticamente 13 profili Vendors su Vestiaire Collective:
- Numero di articoli in vendita
- Numero totale di vendite
- Calcolo delle differenze giornaliere
- Aggiornamento automatico del Google Sheet

## 📊 Profili Monitorati

1. **Rediscover** (2039815)
2. **Volodymyr** (5924329)
3. **stephanie** (9168643)
4. **Mark** (13442939)
5. **A Retro Tale** (5537180)
6. **Lapsa** (11345596)
7. **Hugo** (21940019)
8. **Clara** (27862876)
9. **Baggy Vintage** (18106856)
10. **Vintageandkickz** (19199976)
11. **Vintage & Modern** (29517320)
12. **Plamexs** (8642167)
13. **The Brand Collector** (4085582)

## 🚀 Funzionalità

- ✅ **Web Scraping automatico** dei profili Vestiaire
- ✅ **Calcolo differenze** giornaliere
- ✅ **Aggiornamento Google Sheets** automatico
- ✅ **Esecuzione biquotidiana** alle 11:30 e 23:30 (GitHub Actions)
- ✅ **Logging** degli errori
- ✅ **Notifiche** in caso di problemi
- ✅ **Colonna diff vendite mensili** in ogni tab mensile
- ✅ **Tab Overview** con vista panoramica dei totali mensili

## 🛠️ Stack Tecnologico

- **Python 3.9+**
- **Selenium** per web scraping
- **Google Sheets API** per l'aggiornamento
- **GitHub Actions** per l'automazione
- **BeautifulSoup** per parsing HTML

## 📁 Struttura Progetto

```
vestiaire-monitor/
├── .github/
│   └── workflows/
│       └── daily_update.yml
├── src/
│   ├── scraper.py
│   ├── sheets_updater.py
│   └── main.py
├── config.py
├── requirements.txt
└── README.md
```

## 🔧 Setup

### 1. Configurazione Google Sheets API

1. **Crea un progetto Google Cloud**
2. **Abilita Google Sheets API**
3. **Crea un Service Account**
4. **Scarica il file JSON delle credenziali**

### 2. Configurazione GitHub Secrets

Aggiungi il file JSON delle credenziali come secret:
- **Nome**: `GOOGLE_SHEETS_CREDENTIALS`
- **Valore**: Contenuto del file JSON delle credenziali

### 3. Configurazione Profili

Modifica `config.py` per aggiungere/rimuovere profili:

```python
VESTIAIRE_PROFILES = {
    "Nome Profilo": "ID_Profilo",
    # ... altri profili
}
```

### 4. Esecuzione

- **Automatica**: GitHub Actions alle 11:30 e 23:30 CET
- **Manuale**: `python src/main.py`
- **Test**: `python src/main.py test-overview`

## 📈 Google Sheet

[Update Vestiaire](https://docs.google.com/spreadsheets/d/1sWmvdbEgzLCyaNk5XRDHOFTA5KY1RGeMBIqouXvPJ34/edit?usp=sharing)

### Struttura del Foglio

#### Tab Mensili (es. july)
- **Colonna A**: Profilo
- **Colonna B**: Diff Vendite [Mese] (somma mensile)
- **Colonna C**: URL
- **Colonne D+**: Dati giornalieri (articoli, vendite, diff stock, diff vendite)

#### Tab Overview
- **Righe**: Profili
- **Colonne**: Mesi
- **Valori**: Totali mensili delle diff vendite

## ⏰ Scheduling

- **Frequenza**: Due volte al giorno alle 11:30 e 23:30 (CET)
- **Piattaforma**: GitHub Actions
- **Costo**: Gratuito

## 🚨 Risoluzione Problemi

### Errore "Chrome not found"
- Il workflow GitHub Actions installa automaticamente Chrome
- Per test locale: `brew install google-chrome` (macOS)

### Errore "Google Sheets API"
- Verifica che l'API sia abilitata nel progetto Google Cloud
- Controlla che le credenziali siano corrette
- Verifica i permessi del service account

### Errore "Rate limiting"
- Il sistema include pause tra le richieste
- Se persiste, aumenta `delay_between_requests` in `config.py`

### Logs e Debug
- I logs sono salvati come artifacts in GitHub Actions
- Per debug locale: `python src/main.py` con logging DEBUG

## 📝 Logs

I logs di esecuzione sono disponibili nella sezione Actions di GitHub.

## 🔄 Manutenzione

### Aggiornamento Dipendenze
```bash
pip install --upgrade -r requirements.txt
```

### Monitoraggio Errori
- Il sistema crea automaticamente issues GitHub in caso di errore
- Controlla regolarmente i logs

## 📞 Supporto

Per problemi o domande:
1. Controlla i logs in GitHub Actions
2. Verifica la configurazione in `config.py`
3. Testa localmente con `python src/main.py test` 