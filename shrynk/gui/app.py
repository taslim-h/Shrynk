from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from shrynk.gui.compress_tab import CompressTab
from shrynk.gui.decompress_tab import DecompressTab
from shrynk.gui.theme import BG_INPUT, BORDER, TEXT_ACCENT, TEXT_PRIMARY, TEXT_SECONDARY


class ShrynkWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Shrynk")
        self.setFixedSize(520, 620)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_header())

        tabs = QTabWidget()
        tabs.addTab(CompressTab(), "Compress")
        tabs.addTab(DecompressTab(), "Decompress")
        layout.addWidget(tabs)

        self.setCentralWidget(container)
        self._center_on_screen()

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setStyleSheet(f"border-bottom: 1px solid {BORDER};")

        wrapper = QHBoxLayout(header)
        wrapper.setContentsMargins(20, 16, 20, 14)
        wrapper.setSpacing(12)

        icon = QLabel("+")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(17, 17)
        icon.setStyleSheet(
            f"background: {BG_INPUT}; border: 1px solid {TEXT_ACCENT}; border-radius: 4px; color: {TEXT_ACCENT}; font-weight: bold;"
        )

        title = QLabel("Shrynk")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 500;")

        subtitle = QLabel("Lossless text file compression")
        subtitle.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")

        text_wrap = QWidget()
        text_layout = QVBoxLayout(text_wrap)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)

        wrapper.addWidget(icon, alignment=Qt.AlignTop)
        wrapper.addWidget(text_wrap, 1)
        return header

    def _center_on_screen(self) -> None:
        frame = self.frameGeometry()
        screen = self.screen()
        if screen is None:
            return
        center = screen.availableGeometry().center()
        frame.moveCenter(center)
        self.move(frame.topLeft())
