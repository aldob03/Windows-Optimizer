import os, sys, subprocess
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFrame, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QListWidget, QListWidgetItem, QProgressBar, QAbstractItemView
)
from core.system_info import snapshot
from core import cleaner, startup, uninstaller, processes, optimizer

APP_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "WindowsOptimizer"
BACKUP_DIR = APP_DIR / "backups"

STYLE = """
QWidget { background:#11151d; color:#e8edf5; font-family:'Segoe UI'; font-size:10pt; }
QFrame#sidebar { background:#171e29; border:0; }
QLabel#brand { font-size:19pt; font-weight:700; color:#ffffff; padding:12px; }
QLabel#heading { font-size:20pt; font-weight:700; color:#ffffff; }
QLabel#muted { color:#9aa8ba; }
QPushButton { background:#202b3b; border:1px solid #2c3a4e; border-radius:8px; padding:10px 14px; text-align:left; }
QPushButton:hover { background:#2a3b52; }
QPushButton#primary { background:#3978e8; border:0; font-weight:600; }
QPushButton#primary:hover { background:#4b89f4; }
QTableWidget { background:#171e29; alternate-background-color:#1c2634; gridline-color:#2b3748; border:1px solid #2b3748; border-radius:8px; }
QHeaderView::section { background:#202b3b; color:#cbd5e1; padding:8px; border:0; }
QProgressBar { background:#202b3b; border:0; border-radius:5px; height:10px; text-align:center; }
QProgressBar::chunk { background:#3978e8; border-radius:5px; }
"""

def fmt_bytes(n):
    for unit in ("B","KB","MB","GB","TB"):
        if n < 1024 or unit == "TB": return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Windows Optimizer")
        self.resize(1180, 760)
        self.setMinimumSize(940, 620)
        self.setStyleSheet(STYLE)
        self.clean_items = []
        self.stack = QStackedWidget()
        shell = QWidget(); layout = QHBoxLayout(shell); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        side = QFrame(); side.setObjectName("sidebar"); side.setFixedWidth(220)
        sl = QVBoxLayout(side)
        brand = QLabel("Windows\nOptimizer"); brand.setObjectName("brand"); sl.addWidget(brand)
        self.nav = []
        for label, idx in [("Panoramica",0),("Pulizia sistema",1),("Avvio Windows",2),("Programmi",3),("Processi",4),("Ottimizzazioni",5)]:
            b = QPushButton(label); b.clicked.connect(lambda checked=False, i=idx: self.show_page(i)); sl.addWidget(b); self.nav.append(b)
        sl.addStretch()
        sl.addWidget(QLabel("Modalità guidata • v1.0", objectName="muted"))
        layout.addWidget(side); layout.addWidget(self.stack, 1)
        self.setCentralWidget(shell)
        self.pages = [self.dashboard_page(), self.cleaner_page(), self.startup_page(),
                      self.programs_page(), self.processes_page(), self.tools_page()]
        for p in self.pages: self.stack.addWidget(p)
        self.show_page(0)
        self.timer = QTimer(self); self.timer.timeout.connect(self.refresh_dashboard); self.timer.start(2500)

    def page_base(self, title, subtitle=""):
        w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(28,24,28,24); l.setSpacing(14)
        h = QLabel(title); h.setObjectName("heading"); l.addWidget(h)
        if subtitle:
            s = QLabel(subtitle); s.setObjectName("muted"); l.addWidget(s)
        return w, l

    def show_page(self, idx):
        self.stack.setCurrentIndex(idx)
        if idx == 0: self.refresh_dashboard()
        elif idx == 2: self.load_startup()
        elif idx == 3: self.load_programs()
        elif idx == 4: self.load_processes()

    def dashboard_page(self):
        w,l = self.page_base("Panoramica", "Una vista rapida dello stato delle risorse del computer.")
        self.status = QLabel("Rilevamento in corso…"); self.status.setStyleSheet("font-size:13pt;")
        l.addWidget(self.status)
        self.bars = {}
        for key, label in [("cpu","CPU"),("ram","Memoria RAM"),("disk","Disco di sistema")]:
            row = QHBoxLayout(); row.addWidget(QLabel(label)); bar = QProgressBar(); bar.setRange(0,100); row.addWidget(bar,1)
            self.bars[key] = bar; l.addLayout(row)
        btn = QPushButton("Apri analisi pulizia"); btn.setObjectName("primary"); btn.clicked.connect(lambda: self.show_page(1)); l.addWidget(btn)
        l.addStretch()
        return w

    def refresh_dashboard(self):
        try:
            d = snapshot()
            self.status.setText(f"{d['os']}    •    RAM disponibile: {fmt_bytes(d['ram_total']-d['ram_used'])}    •    Disco libero: {fmt_bytes(d['disk_free'])}")
            for k in self.bars: self.bars[k].setValue(int(d[k]))
        except Exception as e:
            self.status.setText(f"Impossibile leggere le risorse: {e}")

    def cleaner_page(self):
        w,l = self.page_base("Pulizia sistema", "Analizza cartelle temporanee e cache selezionate. I file vengono mostrati prima di ogni eliminazione.")
        row = QHBoxLayout()
        std = QPushButton("Analisi standard"); std.setObjectName("primary"); std.clicked.connect(lambda: self.scan_clean(False))
        adv = QPushButton("Analisi avanzata"); adv.clicked.connect(lambda: self.scan_clean(True))
        row.addWidget(std); row.addWidget(adv); l.addLayout(row)
        self.clean_summary = QLabel("Nessuna analisi eseguita."); self.clean_summary.setObjectName("muted"); l.addWidget(self.clean_summary)
        self.clean_table = QTableWidget(0,3); self.clean_table.setHorizontalHeaderLabels(["Seleziona","Dimensione","Percorso"])
        self.clean_table.horizontalHeader().setSectionResizeMode(2,QHeaderView.Stretch)
        self.clean_table.setSelectionBehavior(QAbstractItemView.SelectRows); l.addWidget(self.clean_table,1)
        delete = QPushButton("Elimina file selezionati…"); delete.setObjectName("primary"); delete.clicked.connect(self.delete_clean)
        l.addWidget(delete)
        return w

    def scan_clean(self, advanced):
        QApplication_process_events()
        try:
            self.clean_items = cleaner.scan(advanced=advanced)
            self.clean_table.setRowCount(len(self.clean_items))
            total = 0
            for i, item in enumerate(self.clean_items):
                from PySide6.QtWidgets import QTableWidgetItem
                cb = QTableWidgetItem(); cb.setFlags(Qt.ItemIsUserCheckable|Qt.ItemIsEnabled); cb.setCheckState(Qt.Checked)
                self.clean_table.setItem(i,0,cb)
                self.clean_table.setItem(i,1,QTableWidgetItem(fmt_bytes(item.size)))
                self.clean_table.setItem(i,2,QTableWidgetItem(item.path))
                total += item.size
            self.clean_summary.setText(f"{len(self.clean_items)} file trovati • Totale: {fmt_bytes(total)} • Modalità {'avanzata' if advanced else 'standard'}")
        except Exception as e:
            QMessageBox.critical(self,"Errore analisi",str(e))

    def delete_clean(self):
        selected = []
        for i, item in enumerate(self.clean_items):
            if self.clean_table.item(i,0).checkState() == Qt.Checked:
                selected.append(item.path)
        if not selected:
            QMessageBox.information(self,"Pulizia","Seleziona almeno un file."); return
        answer = QMessageBox.warning(self,"Conferma eliminazione",
            f"Stai per eliminare {len(selected)} file temporanei/cache.\nL'operazione non è annullabile. Continuare?",
            QMessageBox.Yes|QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes: return
        deleted, errors = cleaner.delete_candidates(selected)
        QMessageBox.information(self,"Pulizia completata",f"Eliminati: {len(deleted)}\nNon eliminati: {len(errors)}")
        self.scan_clean(False)

    def startup_page(self):
        w,l = self.page_base("Avvio Windows", "Voci registrate nelle chiavi Run del registro. Le modifiche richiedono conferma e vengono salvate in un backup.")
        self.start_table = QTableWidget(0,4); self.start_table.setHorizontalHeaderLabels(["Nome","Ambito","Comando",""])
        self.start_table.horizontalHeader().setSectionResizeMode(2,QHeaderView.Stretch); l.addWidget(self.start_table,1)
        btn = QPushButton("Disattiva voce selezionata…"); btn.setObjectName("primary"); btn.clicked.connect(self.disable_selected_startup); l.addWidget(btn)
        return w

    def load_startup(self):
        rows = startup.list_startup(); self.start_table.setRowCount(len(rows)); self.start_rows = rows
        for i,r in enumerate(rows):
            for j,k in enumerate(("name","scope","command")): self.start_table.setItem(i,j,QTableWidgetItem(r[k]))

    def disable_selected_startup(self):
        row = self.start_table.currentRow()
        if row < 0: QMessageBox.information(self,"Avvio","Seleziona una voce."); return
        item = self.start_rows[row]
        ans = QMessageBox.warning(self,"Disattivazione",f"Rimuovere dall'avvio automatico questa voce?\n\n{item['name']}\n{item['command']}\n\nVerrà creato un backup ripristinabile.",
                                  QMessageBox.Yes|QMessageBox.No, QMessageBox.No)
        if ans != QMessageBox.Yes: return
        try:
            backup = startup.disable_startup(item, BACKUP_DIR)
            QMessageBox.information(self,"Completato",f"Voce disattivata.\nBackup: {backup}")
            self.load_startup()
        except Exception as e: QMessageBox.critical(self,"Errore",str(e))

    def programs_page(self):
        w,l = self.page_base("Programmi installati", "Elenco delle applicazioni registrate in Windows. Windows Optimizer non disinstalla autonomamente i programmi.")
        self.program_table = QTableWidget(0,3); self.program_table.setHorizontalHeaderLabels(["Programma","Versione","Editore"])
        self.program_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch); self.program_table.horizontalHeader().setSectionResizeMode(2,QHeaderView.Stretch)
        l.addWidget(self.program_table,1)
        btn = QPushButton("Avvia disinstallatore ufficiale…"); btn.setObjectName("primary"); btn.clicked.connect(self.launch_uninstaller); l.addWidget(btn)
        return w

    def load_programs(self):
        self.program_rows = uninstaller.list_programs(); self.program_table.setRowCount(len(self.program_rows))
        for i,r in enumerate(self.program_rows):
            for j,k in enumerate(("name","version","publisher")): self.program_table.setItem(i,j,QTableWidgetItem(r[k]))

    def launch_uninstaller(self):
        row = self.program_table.currentRow()
        if row < 0: QMessageBox.information(self,"Programmi","Seleziona un programma."); return
        p = self.program_rows[row]; command = p.get("quiet") or p.get("uninstall")
        if not command: QMessageBox.information(self,"Programmi","Non è registrato un comando di disinstallazione."); return
        ans = QMessageBox.warning(self,"Avvio disinstallazione",
            f"Verrà avviato il disinstallatore registrato di:\n{p['name']}\n\nControlla attentamente le richieste del programma. Continuare?",
            QMessageBox.Yes|QMessageBox.No, QMessageBox.No)
        if ans != QMessageBox.Yes: return
        try: subprocess.Popen(command, shell=True)
        except Exception as e: QMessageBox.critical(self,"Errore",str(e))

    def processes_page(self):
        w,l = self.page_base("Processi", "Processi in esecuzione ordinati per consumo di memoria. Nessun processo viene terminato automaticamente.")
        self.proc_table = QTableWidget(0,3); self.proc_table.setHorizontalHeaderLabels(["Nome","PID","Memoria RAM"])
        self.proc_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch); l.addWidget(self.proc_table,1)
        btn = QPushButton("Aggiorna elenco"); btn.clicked.connect(self.load_processes); l.addWidget(btn)
        return w

    def load_processes(self):
        rows = processes.list_processes(); self.proc_table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            self.proc_table.setItem(i,0,QTableWidgetItem(r["name"]))
            self.proc_table.setItem(i,1,QTableWidgetItem(str(r["pid"])))
            self.proc_table.setItem(i,2,QTableWidgetItem(fmt_bytes(r["memory"])))

    def tools_page(self):
        w,l = self.page_base("Ottimizzazioni", "Collegamenti agli strumenti e alle impostazioni ufficiali di Windows.")
        for label,target in optimizer.TOOLS:
            b = QPushButton(label); b.clicked.connect(lambda checked=False,t=target: self.open_tool(t)); l.addWidget(b)
        l.addStretch()
        return w

    def open_tool(self,target):
        try: optimizer.open_tool(target)
        except Exception as e: QMessageBox.warning(self,"Strumento non disponibile",str(e))

def QApplication_process_events():
    from PySide6.QtWidgets import QApplication
    QApplication.processEvents()
