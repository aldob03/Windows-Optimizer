import os, winreg

UNINSTALL_PATHS = [
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
]

def list_programs():
    if os.name != "nt":
        return []
    result = []
    for hive, base in UNINSTALL_PATHS:
        try:
            with winreg.OpenKey(hive, base) as parent:
                for i in range(winreg.QueryInfoKey(parent)[0]):
                    try:
                        sub = winreg.EnumKey(parent, i)
                        with winreg.OpenKey(parent, sub) as key:
                            def read(n):
                                try: return winreg.QueryValueEx(key, n)[0]
                                except OSError: return ""
                            name = read("DisplayName")
                            if name:
                                result.append({
                                    "name": str(name), "version": str(read("DisplayVersion")),
                                    "publisher": str(read("Publisher")),
                                    "uninstall": str(read("UninstallString")),
                                    "quiet": str(read("QuietUninstallString")),
                                })
                    except OSError:
                        continue
        except OSError:
            continue
    # Deduplicate repeated 32/64-bit registry entries.
    seen, unique = set(), []
    for p in result:
        k = (p["name"].lower(), p["version"])
        if k not in seen:
            seen.add(k); unique.append(p)
    return sorted(unique, key=lambda x: x["name"].lower())
