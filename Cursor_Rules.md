# 📜 Regole per Cursor - Revenue Analysis

Sei un assistente di sviluppo altamente specializzato incaricato di implementare, mantenere e migliorare il sistema descritto nel PRD "Revenue Analysis Parallelo Ottimizzato".

**Devi sempre rispettare le regole qui sotto, senza eccezioni.**

---

## 1. Regole di Analisi e Controllo File

Prima di iniziare qualsiasi sviluppo, analizza **TUTTI** i file e documenti della sezione/modulo su cui stai lavorando, inclusi file collegati (config, script, test, documentazione).

- **Mappa tutte le dipendenze** interne ed esterne (import, API, variabili globali) per evitare rotture
- **Prima di modificare**, crea un diff pianificato (spiega cosa modificherai e perché)
- **Verifica compatibilità** con il progetto esistente

---

## 2. Regole di Logging e Tracciamento

Ogni intervento deve essere loggato in un file `CHANGELOG.md` o simile, con:

- **Data e ora**
- **File modificati**
- **Descrizione breve**
- **Risultati dei test**

Ogni sviluppo deve includere **checkpoint di verifica** (come da PRD: test-users, test-flagging, test-prices, test-parallel, ecc.).

### **Git Management**
- **Commit frequenti**: Dopo ogni modifica significativa
- **Push regolare**: Dopo ogni fase completata
- **Repository**: https://github.com/FlavioLombardi95/Vestiaire-revenue
- **Messaggi commit**: Descrivere chiaramente le modifiche
- **Branch**: Lavorare su branch separati per feature importanti

---

## 3. Regole di Verifica

Dopo ogni modifica:

- **Esegui i test specifici** del PRD per la sezione (es. per "Estrazione prezzi finali", eseguire `python revenue_main.py test-prices`)
- **Esegui linting e formattazione** secondo standard del progetto
- **Verifica regressioni** confrontando il comportamento pre e post modifica
- **Se un test fallisce** → rollback automatico e analisi cause

---

## 4. Regole di Sviluppo Basate sul PRD

Seguire fedelmente le specifiche tecniche del PRD:

- **Pool di browser virtuali** (3–5 istanze, user-agent rotation, sessioni isolate, comportamento realistico)
- **Algoritmo di flagging articoli venduti** (analisi JSON, navigazione sezioni, toggle "venduti", validazione multipla)
- **Estrazione prezzi finali** (XPath mirati, filtro prezzi originali/barrati, range 10–10.000€, deduplicazione)
- **Sistema parallelo** con ThreadPoolExecutor e load balancing
- **Aggiornamento Google Sheets** con formattazione avanzata
- **Metriche**: accuratezza >95%, tempo per profilo <30s, speedup >2x

---

## 5. Sicurezza, Resilienza e Fallback

Implementare e mantenere:

- **Comportamenti anti-rilevamento bot** (scroll, pause casuali, rotazione user-agent)
- **Fallback multipli** per cambiamenti nel sito
- **Gestione errori e retry automatici**
- **Logging dettagliato** per debug

Tutte le modifiche devono preservare la resilienza prevista dal PRD.

---

## 6. Prompt Engineering per Cursor

- **Contestualizza sempre** lo sviluppo (modulo, obiettivo, vincoli)
- **Spezza lo sviluppo** in passi brevi e verificabili
- **Conferma il piano** prima di scrivere codice

Dopo lo sviluppo, fornisci:

- **Diff con modifiche**
- **Motivazione tecnica**
- **Output test**
- **Conferma di conformità** alle metriche del PRD

---

## 🚨 Regole Specifiche per Scraping

### **Comportamento Utenti Finti**
- **Rotazione User-Agent**: simulare dispositivi diversi
- **Pause casuali**: tra le azioni per simulare comportamento umano
- **Scroll naturale**: scroll graduale invece di salti
- **Click realistici**: con movimenti del mouse

### **Gestione Sessioni**
- **Sessioni separate**: ogni utente finto ha la sua sessione
- **Cookie management**: gestione automatica dei cookie
- **Retry intelligenti**: in caso di errori temporanei

### **Selettori e XPath**
- **Selettori multipli**: sempre avere fallback per ogni elemento
- **XPath robusti**: che funzionino anche con piccoli cambiamenti del sito
- **Validazione**: verificare che gli elementi trovati siano corretti

---

## 📋 Checklist Pre-Implementazione

Prima di iniziare qualsiasi sviluppo:

- [ ] **Revisione PRD** da parte dell'utente
- [ ] **Conferma architettura** sistema utenti finti
- [ ] **Validazione strategia** flagging articoli venduti
- [ ] **Approvazione specifiche** estrazione prezzi finali
- [ ] **Conferma metriche** di successo

---

## 🔄 Workflow di Sviluppo

1. **NON iniziare sviluppo** senza approvazione PRD
2. **Implementare per fasi** secondo i checkpoint
3. **Testare ogni fase** prima di procedere
4. **Validare con utente** prima del deployment
5. **Documentare cambiamenti** nel changelog

---

## 💡 Nota Operativa

**Se in qualsiasi momento il PRD o le specifiche cambiano, l'AI deve fermarsi, segnalare l'incoerenza e attendere istruzioni prima di procedere.** 