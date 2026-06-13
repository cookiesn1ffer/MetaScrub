"""Dark terminal theme: colors and QSS stylesheet for the desktop UI."""

BG = "#0a0a0a"
PANEL = "#111315"
BORDER = "#232323"
ACCENT = "#00ff88"
FG = "#e6e6e6"
MUTED = "#7a7a7a"
ERROR = "#ff5c5c"

FONT_FAMILY = "JetBrains Mono"
FONT_FALLBACK = "Courier New"
FONT_SIZE = 11

STYLESHEET = f"""
QWidget {{
    background-color: {BG};
    color: {FG};
    font-family: "{FONT_FAMILY}", "{FONT_FALLBACK}", monospace;
    font-size: {FONT_SIZE}pt;
}}

QMainWindow {{
    background-color: {BG};
}}

#TitleLabel {{
    color: {ACCENT};
    font-size: 22pt;
    font-weight: bold;
}}

#SubtitleLabel {{
    color: {MUTED};
    font-size: 10pt;
}}

#SectionLabel {{
    color: {ACCENT};
    font-size: 11pt;
    font-weight: bold;
}}

DropZone {{
    border: 2px dashed {ACCENT};
    border-radius: 10px;
    background-color: {PANEL};
}}

DropZone[dragActive="true"] {{
    background-color: rgba(0, 255, 136, 30);
}}

#DropZoneIcon {{
    color: {ACCENT};
    font-size: 16pt;
    font-weight: bold;
    background: transparent;
}}

#DropZoneLabel {{
    color: {FG};
    font-size: 12pt;
    background: transparent;
}}

#DropZoneLink {{
    color: {ACCENT};
    background: transparent;
}}

#DropZoneHint {{
    color: {MUTED};
    font-size: 9pt;
    background: transparent;
}}

QPushButton {{
    border: 1px solid {ACCENT};
    border-radius: 4px;
    background-color: transparent;
    color: {ACCENT};
    padding: 8px 16px;
}}

QPushButton:hover {{
    background-color: {ACCENT};
    color: #000000;
}}

QPushButton:pressed {{
    background-color: {ACCENT};
    color: #000000;
}}

QPushButton:disabled {{
    border-color: {BORDER};
    color: {MUTED};
}}

#DeleteButton {{
    padding: 2px 10px;
    font-size: 9pt;
    min-width: 60px;
    border-color: {ERROR};
    color: {ERROR};
}}

#DeleteButton:hover {{
    background-color: {ERROR};
    color: #000000;
}}

QProgressBar {{
    border: 1px solid {BORDER};
    border-radius: 4px;
    background-color: {PANEL};
    text-align: center;
    color: {FG};
    height: 22px;
}}

QProgressBar::chunk {{
    background-color: {ACCENT};
    border-radius: 3px;
}}

#ResultPanel {{
    border: 1px solid {ACCENT};
    border-radius: 8px;
    background-color: {PANEL};
}}

#ResultPanel[errorState="true"] {{
    border: 1px solid {ERROR};
}}

#ResultHeader {{
    color: {ACCENT};
    font-size: 12pt;
    font-weight: bold;
    background: transparent;
}}

#ResultHeader[errorState="true"] {{
    color: {ERROR};
}}

#MetaLabel {{
    color: {MUTED};
    background: transparent;
}}

#MetaLabel .value {{
    color: {FG};
}}

#FieldsLabel {{
    color: {FG};
    background: transparent;
}}

#FieldsLabel[errorState="true"] {{
    color: {ERROR};
}}

QTableWidget {{
    background-color: {BG};
    alternate-background-color: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 6px;
    gridline-color: transparent;
}}

QHeaderView::section {{
    background-color: {PANEL};
    color: {ACCENT};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 6px 8px;
    font-weight: 500;
}}

QTableWidget::item {{
    border: none;
    padding: 4px 8px;
}}

QTableWidget::item:selected {{
    background-color: {PANEL};
    color: {FG};
}}

QScrollBar:vertical {{
    background: {BG};
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 20px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QToolTip {{
    background-color: {PANEL};
    color: {FG};
    border: 1px solid {BORDER};
}}
"""
