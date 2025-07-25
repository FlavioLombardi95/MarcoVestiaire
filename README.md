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
├── requirements.txt
└── README.md
```

## 🔧 Setup

1. **Clona il repository**
2. **Configura Google Sheets API**
3. **Aggiungi secrets a GitHub**
4. **Push del codice**

## 📈 Google Sheet

[Update Vestiaire](https://docs.google.com/spreadsheets/d/1sWmvdbEgzLCyaNk5XRDHOFTA5KY1RGeMBIqouXvPJ34/edit?usp=sharing)

## ⏰ Scheduling

- **Frequenza**: Due volte al giorno alle 11:30 e 23:30 (CET)
- **Piattaforma**: GitHub Actions
- **Costo**: Gratuito

## 📝 Logs

I logs di esecuzione sono disponibili nella sezione Actions di GitHub. 