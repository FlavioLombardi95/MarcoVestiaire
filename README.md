# Vestiaire Monitor - Automazione Google Sheets

Sistema di automazione per monitorare i profili Vendors su Vestiaire Collective e aggiornare automaticamente un Google Sheet ogni giorno.

## 🎯 Obiettivo

Monitorare automaticamente 11 profili Vendors su Vestiaire Collective:
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
7. **Bag** (3770739)
8. **Clara** (27862876)
9. **Baggy Vintage** (18106856)
10. **Vintageandkickz** (19199976)
11. **Vintage & Modern** (29517320)

## 🚀 Funzionalità

- ✅ **Web Scraping automatico** dei profili Vestiaire
- ✅ **Calcolo differenze** giornaliere
- ✅ **Aggiornamento Google Sheets** automatico
- ✅ **Esecuzione giornaliera** alle 9:00 AM (GitHub Actions)
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

- **Frequenza**: Ogni giorno alle 9:00 AM (CET)
- **Piattaforma**: GitHub Actions
- **Costo**: Gratuito

## 📝 Logs

I logs di esecuzione sono disponibili nella sezione Actions di GitHub. 