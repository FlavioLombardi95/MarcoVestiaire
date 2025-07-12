# Setup Vestiaire Monitor

Guida completa per configurare l'automazione del monitoraggio Vestiaire Collective.

## 🚀 Setup Rapido

### 1. Clona il Repository

```bash
git clone https://github.com/FlavioLombardi95/MarcoVestiaire.git
cd MarcoVestiaire
```

### 2. Configura Google Sheets API

#### Passo 1: Crea un Progetto Google Cloud
1. Vai su [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuovo progetto o seleziona uno esistente
3. Abilita l'API Google Sheets

#### Passo 2: Crea un Service Account
1. Vai su "IAM & Admin" > "Service Accounts"
2. Clicca "Create Service Account"
3. Dai un nome (es. "vestiaire-monitor")
4. Clicca "Create and Continue"
5. Assegna il ruolo "Editor" per Google Sheets
6. Clicca "Done"

#### Passo 3: Scarica le Credenziali
1. Clicca sul service account creato
2. Vai su "Keys" > "Add Key" > "Create new key"
3. Seleziona "JSON"
4. Scarica il file JSON

#### Passo 4: Condividi il Google Sheet
1. Apri il [Google Sheet](https://docs.google.com/spreadsheets/d/1sWmvdbEgzLCyaNk5XRDHOFTA5KY1RGeMBIqouXvPJ34/edit?usp=sharing)
2. Clicca "Share"
3. Aggiungi l'email del service account (nel file JSON, campo `client_email`)
4. Assegna i permessi "Editor"

### 3. Configura GitHub Secrets

1. Vai su [GitHub Repository](https://github.com/FlavioLombardi95/MarcoVestiaire)
2. Vai su "Settings" > "Secrets and variables" > "Actions"
3. Clicca "New repository secret"
4. Nome: `GOOGLE_SHEETS_CREDENTIALS`
5. Valore: Copia tutto il contenuto del file JSON delle credenziali

### 4. Test Locale (Opzionale)

```bash
# Installa le dipendenze
pip install -r requirements.txt

# Testa lo scraping
cd src
python main.py test

# Testa Google Sheets (richiede credenziali)
export GOOGLE_SHEETS_CREDENTIALS='{"type": "service_account", ...}'
python main.py test-sheets
```

## 🔧 Configurazione Avanzata

### Modificare i Profili Monitorati

Modifica il file `config.py`:

```python
VESTIAIRE_PROFILES = {
    "Nuovo Profilo": "12345678",
    # ... altri profili
}
```

### Cambiare l'Orario di Esecuzione

Modifica il file `.github/workflows/daily_update.yml`:

```yaml
schedule:
  # Esegui alle 10:00 AM (CET)
  - cron: '0 9 * * *'
```

### Configurazione Logging

Modifica `config.py`:

```python
LOGGING_CONFIG = {
    "level": "DEBUG",  # Per più dettagli
    "file": "custom_log.log"
}
```

## 📊 Struttura Google Sheet

Il sistema creerà automaticamente:

### Foglio Principale (Foglio1)
- Profilo | URL | Articoli | Vendite | Data
- Dati giornalieri per ogni profilo
- Riga dei totali

### Foglio Riepilogo
- Data | Profilo | Articoli | Vendite | Timestamp
- Storico completo dei dati

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
- Per debug locale: `python main.py` con logging DEBUG

## 📈 Monitoraggio

### GitHub Actions
- Vai su "Actions" nel repository
- Controlla l'ultima esecuzione del workflow
- Scarica i logs se necessario

### Google Sheet
- Il foglio viene aggiornato automaticamente ogni giorno
- Controlla la colonna "Data" per verificare gli aggiornamenti

## 🔄 Manutenzione

### Aggiornamento Dipendenze
```bash
pip install --upgrade -r requirements.txt
```

### Backup Credenziali
- Mantieni una copia sicura del file JSON delle credenziali
- Ruota le credenziali periodicamente

### Monitoraggio Errori
- Il sistema crea automaticamente issues GitHub in caso di errore
- Controlla regolarmente i logs

## 📞 Supporto

Per problemi o domande:
1. Controlla i logs in GitHub Actions
2. Verifica la configurazione in `config.py`
3. Testa localmente con `python main.py test` 