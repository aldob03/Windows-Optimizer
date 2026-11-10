# Windows Optimizer

Applicazione desktop guidata per Windows 10/11 x64, realizzata con Python, PySide6 e psutil.

## Stato e limiti della versione iniziale

Questa è una **prima versione sorgente** da collaudare su Windows. Non è ancora un EXE verificato.

Funzioni incluse:
- Dashboard CPU/RAM/disco.
- Scansione di directory temporanee/cache esplicitamente consentite.
- Anteprima, selezione manuale e conferma prima dell'eliminazione.
- Lettura delle voci Run del registro e disattivazione con backup JSON.
- Elenco programmi registrati e avvio del comando di disinstallazione registrato.
- Elenco processi ordinato per RAM.
- Collegamenti alle impostazioni di Windows.

Limitazioni note:
- La gestione delle voci di avvio copre le chiavi Run principali, non tutte le attività pianificate o i servizi.
- La pulizia non include Download, Cestino, Prefetch, cartelle di sistema generiche o dati dei browser non temporanei.
- Il comando di disinstallazione proviene dal registro; viene avviato solo dopo conferma e può richiedere parametri/interazione.
- Il backup di avvio consente il ripristino manuale tramite il modulo `core.startup.restore_startup`.
- Alcune funzioni richiedono Windows e/o privilegi amministrativi.
- Eseguire sempre test su macchina virtuale o PC di prova prima della distribuzione.

## Avvio da sorgente su Windows

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
py main.py
```

## Build one-file con PyInstaller

```powershell
py -m pip install pyinstaller
py -m PyInstaller --noconfirm --clean --windowed --onefile --name "Windows Optimizer" --collect-all PySide6 main.py
```

Output: `dist\\Windows Optimizer.exe`

## Build da Mac tramite GitHub Actions

1. Crea un repository GitHub e carica l'intero contenuto di questa cartella.
2. Apri Actions.
3. Seleziona **Build Windows portable EXE** e avvia il workflow.
4. Scarica l'artifact `Windows-Optimizer-portable`.

L'EXE va comunque provato su Windows 10 e Windows 11, su un account standard e su un account amministratore, prima di considerarlo pronto alla distribuzione.
