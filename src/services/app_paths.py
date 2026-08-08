import os
import sys
from pathlib import Path


APP_NAME = "ReceiptReader"


def user_cache_dir() -> Path:
    """Return a writable per-user cache directory for desktop launches."""
    override = os.environ.get("RECEIPTREADER_CACHE_DIR")
    if override:
        path = Path(override)
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Caches"
        path = root / APP_NAME
    elif sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        path = root / APP_NAME
    else:
        root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        path = root / APP_NAME

    path.mkdir(parents=True, exist_ok=True)
    return path
