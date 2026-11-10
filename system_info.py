import platform
import psutil
import shutil

def snapshot():
    disk = shutil.disk_usage("C:\\" if platform.system() == "Windows" else "/")
    return {
        "os": f"{platform.system()} {platform.release()}",
        "cpu": psutil.cpu_percent(interval=0.25),
        "ram": psutil.virtual_memory().percent,
        "disk": (disk.used / disk.total) * 100 if disk.total else 0,
        "ram_used": psutil.virtual_memory().used,
        "ram_total": psutil.virtual_memory().total,
        "disk_free": disk.free,
        "disk_total": disk.total,
    }
