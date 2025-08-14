# 📄 Product Requirement Document (PRD) - Revenue Analysis Parallelo Ottimizzato

## 🎯 Obiettivo
Implementare un sistema di **web scraping parallelo avanzato** per analizzare i ricavi dei competitor su Vestiaire Collective, utilizzando **utenti "finti"** che simulano comportamenti reali per identificare correttamente gli articoli venduti e i prezzi di vendita finali.

---

## 🚀 Architettura Sistema

### **1. Sistema Utenti Finti Paralleli**
- **Pool di Browser Virtuali**: 3-5 istanze Chrome indipendenti
- **Rotazione User-Agent**: Simulazione di dispositivi diversi (desktop, mobile, tablet)
- **Sessioni Separate**: Ogni utente finto mantiene una sessione isolata
- **Comportamento Realistico**: Scroll, pause, click casuali per evitare rilevamento bot

### **2. Strategia di Identificazione Articoli Venduti**
- **Flagging Intelligente**: Gli utenti finti navigano e "flaggiano" gli articoli venduti
- **Analisi Multi-Livello**:
  - Ricerca nei contatori JSON della pagina
  - Navigazione alle sezioni "venduti" 
  - Click sui toggle "Articoli venduti"
  - Analisi delle card prodotto con stato "venduto"
- **Validazione Cross-Reference**: Conferma vendite tramite multiple fonti

### **3. Estrazione Prezzi di Vendita Finali**
- **Focus sui Prezzi Finali**: Solo prezzi di vendita (non quelli barrati/originali)
- **Selettori Avanzati**: XPath specifici per prezzi finali in card prodotto
- **Filtro Prezzi Ragionevoli**: Range 10€ - 10.000€ per evitare errori
- **Deduplicazione**: Rimozione prezzi duplicati mantenendo ordine cronologico

---

## 📌 Checkpoint di Progetto

### **1. Setup Sistema Utenti Finti**
- [ ] Configurazione pool browser virtuali (3-5 istanze)
- [ ] Implementazione rotazione User-Agent e sessioni
- [ ] Setup comportamenti realistici (scroll, pause, click)
- [ ] **Checkpoint:** Test con `python revenue_main.py test-users` - verifica che ogni utente finto possa navigare indipendentemente

### **2. Implementazione Flagging Articoli Venduti**
- [ ] Sviluppo algoritmo di flagging intelligente
- [ ] Navigazione automatica alle sezioni "venduti"
- [ ] Attivazione toggle "Articoli venduti" con fallback
- [ ] Analisi JSON e contatori pagina
- [ ] **Checkpoint:** Test con `python revenue_main.py test-flagging` - verifica identificazione corretta di 37 vendite per Vintage & Modern

### **3. Estrazione Prezzi di Vendita Finali**
- [ ] Implementazione selettori XPath specifici per prezzi finali
- [ ] Filtro prezzi barrati/originali
- [ ] Validazione range prezzi (10€ - 10.000€)
- [ ] Deduplicazione prezzi
- [ ] **Checkpoint:** Test con `python revenue_main.py test-prices` - verifica estrazione prezzi finali corretti

### **4. Sistema Parallelo Ottimizzato**
- [ ] ThreadPoolExecutor con 3-5 workers (configurabile)
- [ ] Gestione sessioni utenti finti parallele
- [ ] Load balancing tra istanze browser
- [ ] **Checkpoint:** Test con `python revenue_main.py test-parallel` - misura performance vs sequenziale

### **5. Calcolo Ricavi Giornalieri**
- [ ] Somma prezzi venduti per profilo
- [ ] Calcolo differenza rispetto al giorno precedente
- [ ] Validazione coerenza dati
- [ ] **Checkpoint:** Verifica calcolo corretto in tab mensile

### **6. Aggiornamento Google Sheets**
- [ ] Creazione tab mensili con formattazione avanzata
- [ ] Tab `Revenue_Overview` con aggregazione
- [ ] Gestione errori e retry automatici
- [ ] **Checkpoint:** Test con `python revenue_main.py test-sheets`

### **7. Ottimizzazione Performance e Resilienza**
- [ ] Misurazione tempi per profilo
- [ ] Gestione errori e fallback automatici
- [ ] Logging dettagliato per debug
- [ ] **Checkpoint:** Report performance e superamento test stress

### **8. Deployment e Monitoraggio**
- [ ] Esecuzione prima raccolta in produzione
- [ ] Setup monitoraggio continuo
- [ ] **Checkpoint:** Dati popolati correttamente su Google Sheets ufficiale

---

## 🔧 Specifiche Tecniche

### **Gestione Utenti Finti**
```python
# Configurazione pool utenti
USER_POOL_SIZE = 3  # Configurabile
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
]
```

### **Strategia Flagging Articoli Venduti**
1. **Analisi JSON**: Cerca nei `<script type='application/ld+json'>` per contatori venduti
2. **Navigazione Sezioni**: Prova URL `/sold/`, `/venduti/`, `/items/sold/`
3. **Toggle Attivazione**: Click su "Articoli venduti" con fallback
4. **Analisi Contatori**: Cerca pattern "37 venduti", "37 sold" nel testo

### **Estrazione Prezzi Finali**
```python
# Selettori XPath per prezzi finali
FINAL_PRICE_SELECTORS = [
    "//div[contains(@class, 'product-card')]//span[contains(text(), '€') and not(ancestor::*[contains(@class, 'strike')])]",
    "//span[contains(@class, 'final-price') and contains(text(), '€')]",
    "//span[contains(@class, 'sale-price') and contains(text(), '€')]"
]
```

### **Sistema Parallelo**
- **ThreadPoolExecutor**: 3-5 workers configurabili
- **Sessioni Isolate**: Ogni worker ha il suo browser virtuale
- **Load Balancing**: Distribuzione automatica profili tra workers
- **Error Handling**: Retry automatico e fallback sequenziale

---

## 📊 Metriche di Successo

### **Accuratezza Dati**
- ✅ Identificazione corretta vendite reali (37 per Vintage & Modern)
- ✅ Estrazione prezzi di vendita finali (non barrati)
- ✅ Calcolo ricavi accurato

### **Performance**
- ⚡ Tempo medio per profilo: < 30 secondi
- ⚡ Speedup parallelo vs sequenziale: > 2x
- ⚡ Success rate: > 95%

### **Affidabilità**
- 🛡️ Gestione errori robusta
- 🛡️ Fallback automatici
- 🛡️ Logging completo per debug

---

## 🚨 Rischi e Mitigazioni

### **Rischio: Rilevamento Bot**
- **Mitigazione**: Comportamenti realistici, rotazione User-Agent, pause casuali

### **Rischio: Cambiamenti Sito**
- **Mitigazione**: Selettori multipli, fallback, monitoraggio continuo

### **Rischio: Rate Limiting**
- **Mitigazione**: Pool utenti, distribuzione carico, retry intelligenti

---

## 📋 Prossimi Passi

1. **Revisione PRD** da parte dell'utente
2. **Implementazione sistema utenti finti**
3. **Sviluppo algoritmo flagging articoli venduti**
4. **Ottimizzazione estrazione prezzi finali**
5. **Test e validazione sistema parallelo**
6. **Deployment in produzione** 