import psutil

def list_processes():
    rows = []
    for p in psutil.process_iter(["pid", "name", "memory_info", "username"]):
        try:
            info = p.info
            mem = info["memory_info"].rss if info.get("memory_info") else 0
            rows.append({"pid": info["pid"], "name": info.get("name") or "",
                         "memory": mem, "user": info.get("username") or ""})
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return sorted(rows, key=lambda x: x["memory"], reverse=True)
