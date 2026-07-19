"""Koyu tema: tasarim token sabitleri ve global QSS.

Kaynak: design_handoff_controlify_ui/README.md (Design Tokens bolumu).
Ortak parcalar (buton varyantlari, pencere zeminleri) burada; ekrana ozel
stiller ilgili ekranin setupUi'sinde bu token'larla kurulur.

Not: Qt QSS rgba() alfa degerini 0-255 tam sayi bekler; tasarimdaki 0.14
gibi oranlar 255 ile carpilip yuvarlandi (0.14 -> 36).
"""

# Zeminler
BG = "#15171c"  # pencere arkaplani
SURFACE = "#1d2026"  # panel/kart/liste
SURFACE_2 = "#232730"  # chip/ikincil buton zemini
DROP_ZONE_BG = "#181b21"  # dosya birakma alani
FRAME_BG = "#1a1d23"  # frame gelene dek kontrol ekrani zemini

# Cizgiler
BORDER = "#2c313b"
DIVIDER = "#262a33"  # liste ici ayrac
BORDER_HOVER = "#3a4150"

# Metin
TEXT = "#e7eaf1"
MUTED = "#8e95a3"
FAINT = "#565d6b"
BUSY_TEXT = "#6d7482"  # mesgul satir metni

# Vurgu
ACCENT = "#5c8ef0"
ACCENT_HOVER = "#6f9cf3"
ACCENT_TINT = "rgba(92, 142, 240, 36)"  # 0.14

# Durum
GREEN = "#3fb877"  # musait
AMBER = "#d9a13c"  # mesgul
GREEN_RING = "rgba(63, 184, 119, 38)"  # 0.15 — glow yerine dis halka

# Tehlike
DANGER = "#e05d5d"
DANGER_TINT = "rgba(224, 93, 93, 31)"  # 0.12
DANGER_TINT_HOVER = "rgba(224, 93, 93, 51)"  # 0.2
DANGER_TINT_BORDER = "rgba(224, 93, 93, 77)"  # 0.3
DANGER_HOVER_BORDER = "#4a3236"

# Liste satirlari
ROW_HOVER = "#20242c"
ROW_SELECTED = "#242c3e"

# Tipografi
MONO = "Menlo, Consolas, monospace"

# Ortak buton varyantlari: btn.setProperty("variant", "primary"|"ghost"|"danger")
THEME_QSS = f"""
QWidget {{
    color: {TEXT};
    font-size: 13px;
}}
QMainWindow {{
    background-color: {BG};
}}
QDialog {{
    background-color: {SURFACE};
}}

QPushButton[variant="primary"] {{
    background-color: {ACCENT};
    color: #ffffff;
    font-size: 13px;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    padding: 0 28px;
}}
QPushButton[variant="primary"]:hover {{
    background-color: {ACCENT_HOVER};
}}
QPushButton[variant="primary"]:disabled {{
    background-color: {SURFACE_2};
    color: {FAINT};
}}

QPushButton[variant="ghost"] {{
    background-color: transparent;
    color: {MUTED};
    font-size: 12px;
    font-weight: 500;
    border: 1px solid {BORDER};
    border-radius: 7px;
    padding: 6px 16px;
}}
QPushButton[variant="ghost"]:hover {{
    color: {DANGER};
    border-color: {DANGER_HOVER_BORDER};
}}

QPushButton[variant="danger"] {{
    background-color: {DANGER_TINT};
    color: {DANGER};
    font-size: 12px;
    font-weight: 600;
    border: 1px solid {DANGER_TINT_BORDER};
    border-radius: 7px;
    padding: 6px 14px;
}}
QPushButton[variant="danger"]:hover {{
    background-color: {DANGER_TINT_HOVER};
}}
"""
