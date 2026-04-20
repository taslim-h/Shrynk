import sys

from PyQt5.QtWidgets import QApplication

from shrynk.gui.app import ShrynkWindow
from shrynk.gui.theme import (
    BG_BUTTON,
    BG_INPUT,
    BG_PRIMARY,
    BG_PRIMARY_HVR,
    BG_SURFACE,
    BG_WINDOW,
    BORDER,
    TAB_ACTIVE_LINE,
    TEXT_ACCENT,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


def build_stylesheet() -> str:
    return f"""
    QWidget {{
        background: {BG_WINDOW};
        color: {TEXT_PRIMARY};
        font-family: Arial, sans-serif;
    }}
    QMainWindow {{
        background: {BG_WINDOW};
    }}
    QLabel {{
        color: {TEXT_PRIMARY};
    }}
    QLineEdit {{
        background: {BG_INPUT};
        border: 1px solid {BORDER};
        border-radius: 8px;
        color: {TEXT_SECONDARY};
        padding: 10px 12px;
        font-size: 12px;
    }}
    QPushButton {{
        background: {BG_BUTTON};
        border: 1px solid {BORDER};
        border-radius: 8px;
        color: {TEXT_PRIMARY};
        padding: 10px 14px;
        font-size: 12px;
    }}
    QPushButton:hover {{
        border-color: {TEXT_ACCENT};
    }}
    QPushButton:disabled {{
        color: {TEXT_SECONDARY};
    }}
    QPushButton#primaryButton {{
        background: {BG_PRIMARY};
        border: none;
        color: {TEXT_PRIMARY};
        font-size: 14px;
        font-weight: 500;
        padding: 12px 16px;
    }}
    QPushButton#primaryButton:hover {{
        background: {BG_PRIMARY_HVR};
    }}
    QPushButton#primaryButton:disabled {{
        background: {BG_BUTTON};
        color: {TEXT_SECONDARY};
    }}
    QCheckBox {{
        color: {TEXT_SECONDARY};
        font-size: 12px;
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 1px solid {BORDER};
        background: {BG_INPUT};
    }}
    QCheckBox::indicator:checked {{
        background: {TEXT_ACCENT};
        border-color: {TEXT_ACCENT};
    }}
    QTabWidget::pane {{
        border: none;
    }}
    QTabBar::tab {{
        background: {BG_SURFACE};
        color: {TEXT_SECONDARY};
        padding: 12px 18px;
        font-size: 13px;
        border: none;
        border-bottom: 2px solid {BG_SURFACE};
        min-width: 120px;
    }}
    QTabBar::tab:selected {{
        background: {BG_WINDOW};
        color: {TEXT_ACCENT};
        border-bottom: 2px solid {TAB_ACTIVE_LINE};
    }}
    QProgressBar {{
        background: {BG_INPUT};
        border: 1px solid {BORDER};
        border-radius: 99px;
        min-height: 5px;
        max-height: 5px;
    }}
    QProgressBar::chunk {{
        background: {TEXT_ACCENT};
        border-radius: 99px;
    }}
    QMessageBox {{
        background: {BG_WINDOW};
    }}
    """


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(build_stylesheet())
    window = ShrynkWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
