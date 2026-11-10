import os, subprocess

TOOLS = [
    ("Impostazioni di avvio", "ms-settings:startup"),
    ("Archiviazione", "ms-settings:storagesense"),
    ("Alimentazione e batteria", "ms-settings:powersleep"),
    ("App installate", "ms-settings:appsfeatures"),
]

def open_tool(target):
    if os.name != "nt":
        raise OSError("Disponibile solo su Windows")
    if target.startswith("ms-settings:"):
        os.startfile(target)
    else:
        subprocess.Popen(target, shell=False)
