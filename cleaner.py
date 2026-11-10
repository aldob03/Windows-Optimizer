import os
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Iterable

@dataclass
class Candidate:
    path: str
    size: int
    category: str

def _safe_roots(advanced=False):
    roots = [Path(tempfile.gettempdir())]
    local = os.environ.get("LOCALAPPDATA")
    windir = os.environ.get("WINDIR")
    if local:
        roots.extend([Path(local) / "Temp"])
        if advanced:
            roots.extend([
                Path(local) / "Microsoft" / "Windows" / "INetCache",
                Path(local) / "Microsoft" / "Windows" / "WER" / "ReportArchive",
            ])
    if advanced and windir:
        roots.append(Path(windir) / "Temp")
    # Only explicitly approved cache/temp directories are scanned.
    return list(dict.fromkeys(p for p in roots if p.exists() and p.is_dir()))

def _is_safe_child(path: Path, roots: Iterable[Path]):
    try:
        resolved = path.resolve(strict=False)
        for root in roots:
            rr = root.resolve(strict=False)
            if resolved != rr and rr in resolved.parents:
                return True
    except (OSError, RuntimeError):
        pass
    return False

def scan(advanced=False, max_items=5000):
    roots = _safe_roots(advanced)
    found = []
    for root in roots:
        try:
            for current, dirs, names in os.walk(root, topdown=True, followlinks=False):
                dirs[:] = [d for d in dirs if not (Path(current) / d).is_symlink()]
                for name in names:
                    p = Path(current) / name
                    if p.is_symlink() or not _is_safe_child(p, roots):
                        continue
                    try:
                        if not p.is_file():
                            continue
                        size = p.stat().st_size
                        if size:
                            found.append(Candidate(str(p), size, str(root)))
                    except (OSError, PermissionError):
                        continue
                    if len(found) >= max_items:
                        return found
        except (OSError, PermissionError):
            continue
    return found

def delete_candidates(paths):
    deleted, errors = [], []
    roots = _safe_roots(True)
    for raw in paths:
        p = Path(raw)
        if p.is_symlink() or not _is_safe_child(p, roots):
            errors.append((raw, "Percorso non consentito"))
            continue
        try:
            if p.is_file():
                p.unlink()
                deleted.append(raw)
        except (OSError, PermissionError) as exc:
            errors.append((raw, str(exc)))
    return deleted, errors
