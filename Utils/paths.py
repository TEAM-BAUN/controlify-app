import sys
from pathlib import Path

# PyInstaller onefile calisirken dosyalar gecici _MEIPASS dizinine acilir;
# normal calismada proje koku baz alinir (cwd degil, dosya konumu)
_BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))


def asset_path(name: str) -> str:
    return str(_BASE / "assets" / name)
