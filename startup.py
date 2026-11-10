import os, winreg, json
from pathlib import Path

RUN_KEYS = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "Utente"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "Computer"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run", "Computer 32-bit"),
]

def list_startup():
    if os.name != "nt":
        return []
    items = []
    for hive, subkey, scope in RUN_KEYS:
        try:
            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0)) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        items.append({"name": name, "command": str(value), "scope": scope,
                                      "hive": int(hive), "key": subkey, "enabled": True})
                        i += 1
                    except OSError:
                        break
        except OSError:
            pass
    return items

def disable_startup(item, backup_dir):
    if os.name != "nt":
        raise OSError("Funzione disponibile solo su Windows")
    hive = winreg.HKEY_CURRENT_USER if item["hive"] == int(winreg.HKEY_CURRENT_USER) else winreg.HKEY_LOCAL_MACHINE
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / "startup-backup.json"
    existing = []
    if backup.exists():
        try: existing = json.loads(backup.read_text(encoding="utf-8"))
        except Exception: existing = []
    existing.append({k: item[k] for k in ("name", "command", "scope", "hive", "key")})
    backup.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    access = winreg.KEY_SET_VALUE | getattr(winreg, "KEY_WOW64_64KEY", 0)
    with winreg.OpenKey(hive, item["key"], 0, access) as key:
        winreg.DeleteValue(key, item["name"])
    return str(backup)

def restore_startup(backup_file):
    if os.name != "nt":
        raise OSError("Funzione disponibile solo su Windows")
    data = json.loads(Path(backup_file).read_text(encoding="utf-8"))
    restored, errors = [], []
    for item in data:
        hive = winreg.HKEY_CURRENT_USER if item["hive"] == int(winreg.HKEY_CURRENT_USER) else winreg.HKEY_LOCAL_MACHINE
        try:
            access = winreg.KEY_SET_VALUE | getattr(winreg, "KEY_WOW64_64KEY", 0)
            with winreg.OpenKey(hive, item["key"], 0, access) as key:
                winreg.SetValueEx(key, item["name"], 0, winreg.REG_SZ, item["command"])
            restored.append(item["name"])
        except OSError as exc:
            errors.append((item["name"], str(exc)))
    return restored, errors
