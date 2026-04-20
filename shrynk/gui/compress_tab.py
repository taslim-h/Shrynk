from __future__ import annotations

import os
from pathlib import Path
from typing import List, Tuple

from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PyQt5.QtWidgets import (
    QFileDialog,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from shrynk.gui.theme import (
    BG_BUTTON,
    BG_INPUT,
    BG_SURFACE,
    BORDER,
    TEXT_ACCENT,
    TEXT_ERROR,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_SUCCESS,
)
from shrynk.worker import CompressWorker, format_size


class FrequencyBar(QWidget):
    def __init__(self, char: str, pct: float, max_pct: float) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        label = QLabel(self._display_char(char))
        label.setFixedWidth(34)
        label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 11px; font-family: Consolas, monospace;"
        )

        bar_track = QFrame()
        bar_track.setFixedHeight(5)
        bar_track.setStyleSheet(
            f"background: {BG_BUTTON}; border-radius: 99px;"
        )
        bar_layout = QVBoxLayout(bar_track)
        bar_layout.setContentsMargins(0, 0, 0, 0)

        bar_fill = QFrame()
        width_pct = 0 if max_pct == 0 else int((pct / max_pct) * 100)
        bar_fill.setStyleSheet(
            f"background: {TEXT_ACCENT}; border-radius: 99px;"
        )
        bar_fill.setFixedWidth(max(8, width_pct * 2))
        bar_fill.setFixedHeight(5)
        bar_layout.addWidget(bar_fill, alignment=Qt.AlignLeft)

        pct_label = QLabel(f"{pct:>4.1f}%")
        pct_label.setFixedWidth(46)
        pct_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pct_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")

        layout.addWidget(label)
        layout.addWidget(bar_track, 1)
        layout.addWidget(pct_label)

    @staticmethod
    def _display_char(char: str) -> str:
        mapping = {" ": "' '", "\n": r"'\n'", "\t": r"'\t'"}
        return mapping.get(char, repr(char))


class CompressTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.worker = None
        self._progress_animation = None

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 20)
        root.setSpacing(16)

        root.addWidget(self._build_input_section())
        root.addWidget(self._build_output_section())

        self.compress_button = QPushButton("Compress")
        self.compress_button.setObjectName("primaryButton")
        self.compress_button.clicked.connect(self.start_compression)
        root.addWidget(self.compress_button)

        root.addWidget(self._build_progress_section())
        root.addWidget(self._build_results_section(), 1)

    def _build_input_section(self) -> QWidget:
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = self._section_label("Input file")
        layout.addWidget(label)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        self.input_edit = QLineEdit()
        self.input_edit.setReadOnly(True)

        browse = QPushButton("Browse")
        browse.clicked.connect(self.browse_input)

        row.addWidget(self.input_edit, 1)
        row.addWidget(browse)
        layout.addLayout(row)
        return section

    def _build_output_section(self) -> QWidget:
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addWidget(self._section_label("Output file"))

        self.auto_output = QCheckBox("Auto — same folder, rename to .huf")
        self.auto_output.setChecked(True)
        self.auto_output.toggled.connect(self.toggle_output_mode)
        layout.addWidget(self.auto_output)

        self.custom_output_wrap = QWidget()
        custom_layout = QHBoxLayout(self.custom_output_wrap)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.setSpacing(8)

        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)

        browse = QPushButton("Browse")
        browse.clicked.connect(self.browse_output)

        custom_layout.addWidget(self.output_edit, 1)
        custom_layout.addWidget(browse)
        self.custom_output_wrap.hide()
        layout.addWidget(self.custom_output_wrap)
        return section

    def _build_progress_section(self) -> QWidget:
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)

        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")

        self.progress_pct = QLabel("0%")
        self.progress_pct.setStyleSheet(f"color: {TEXT_ACCENT}; font-size: 12px;")

        row.addWidget(self.progress_label)
        row.addStretch(1)
        row.addWidget(self.progress_pct)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)

        layout.addLayout(row)
        layout.addWidget(self.progress_bar)
        return section

    def _build_results_section(self) -> QWidget:
        frame = QFrame()
        frame.setStyleSheet(
            f"background: {BG_SURFACE}; border: 1px solid {BORDER}; border-radius: 8px;"
        )
        outer = QVBoxLayout(frame)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QLabel("Results")
        header.setStyleSheet(
            f"background: {BG_INPUT}; border-bottom: 1px solid {BORDER}; color: {TEXT_SECONDARY}; font-size: 11px; font-weight: 500; padding: 10px 12px;"
        )
        outer.addWidget(header)

        self.results_body = QWidget()
        self.results_body.setStyleSheet(f"background: {BG_SURFACE};")
        self.results_layout = QVBoxLayout(self.results_body)
        self.results_layout.setContentsMargins(12, 12, 12, 12)
        self.results_layout.setSpacing(10)
        outer.addWidget(self.results_body, 1)
        return frame

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text.upper())
        label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px; font-weight: 500;")
        return label

    def browse_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select text file",
            "",
            "Text files (*.txt)",
        )
        if not path:
            return
        self.input_edit.setText(path)
        if self.auto_output.isChecked():
            self.output_edit.setText(self._auto_output_path(path))

    def browse_output(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save compressed file",
            self.output_edit.text() or self._auto_output_path(self.input_edit.text()),
            "Huffman files (*.huf)",
        )
        if path:
            self.output_edit.setText(path)

    def toggle_output_mode(self, checked: bool) -> None:
        self.custom_output_wrap.setVisible(not checked)
        if checked and self.input_edit.text():
            self.output_edit.setText(self._auto_output_path(self.input_edit.text()))

    def _auto_output_path(self, input_path: str) -> str:
        if not input_path:
            return ""
        return str(Path(input_path).with_suffix(".huf"))

    def _resolved_output_path(self) -> str:
        if self.auto_output.isChecked():
            return self._auto_output_path(self.input_edit.text())
        return self.output_edit.text().strip()

    def start_compression(self) -> None:
        input_path = self.input_edit.text().strip()
        error = self._validate_inputs(input_path, self._resolved_output_path())
        if error:
            self._show_error(error)
            return

        output_path = self._resolved_output_path()
        if os.path.exists(output_path):
            if not self._confirm_overwrite(output_path):
                return

        self.compress_button.setDisabled(True)
        self._set_progress(0, "")
        self._clear_results()

        self.worker = CompressWorker(input_path, output_path)
        self.worker.progress.connect(self._set_progress)
        self.worker.finished.connect(self._on_success)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _validate_inputs(self, input_path: str, output_path: str) -> str:
        if not input_path:
            return "Input file not found."
        if not os.path.isfile(input_path):
            return "Input file not found."
        if Path(input_path).suffix.lower() != ".txt":
            return "Not a valid text file."
        if os.path.getsize(input_path) == 0:
            return "File is empty."
        if not output_path:
            return "Output location is not writable."
        if not self._output_writable(output_path):
            return "Output location is not writable."
        return ""

    def _output_writable(self, output_path: str) -> bool:
        target = Path(output_path)
        if target.exists():
            return os.access(str(target), os.W_OK)
        parent = target.parent if str(target.parent) else Path(".")
        return parent.exists() and os.access(str(parent), os.W_OK)

    def _set_progress(self, percent: int, label: str) -> None:
        self.progress_label.setText(label)
        self.progress_pct.setText(f"{percent}%")
        animation = QPropertyAnimation(self.progress_bar, b"value", self)
        animation.setDuration(180)
        animation.setStartValue(self.progress_bar.value())
        animation.setEndValue(percent)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start()
        self._progress_animation = animation

    def _confirm_overwrite(self, output_path: str) -> bool:
        box = QMessageBox(self)
        box.setWindowTitle("Overwrite file")
        box.setText(f"'{Path(output_path).name}' already exists.\nOverwrite it?")
        cancel_button = box.addButton("Cancel", QMessageBox.RejectRole)
        overwrite_button = box.addButton("Overwrite", QMessageBox.AcceptRole)
        box.exec_()
        return box.clickedButton() is overwrite_button and box.clickedButton() is not cancel_button

    def _on_success(self, result: dict) -> None:
        self.compress_button.setDisabled(False)
        self._render_success(result)
        self.worker = None

    def _on_error(self, message: str) -> None:
        self.compress_button.setDisabled(False)
        self._show_error(message)
        self.worker = None

    def _clear_results(self) -> None:
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _show_error(self, message: str) -> None:
        self._set_progress(0, "")
        self._clear_results()

        top = QLabel(f"✗ Error: {message}")
        top.setStyleSheet(f"color: {TEXT_ERROR}; font-size: 12px; font-weight: 500;")
        self.results_layout.addWidget(top)

        detail = QLabel(f"  {message}")
        detail.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        self.results_layout.addWidget(detail)
        self.results_layout.addStretch(1)

    def _render_success(self, result: dict) -> None:
        self._clear_results()
        input_name = Path(result["input_path"]).name
        output_name = Path(result["output_path"]).name
        input_size = result["input_size"]
        output_size = result["output_size"]
        saved = input_size - output_size
        smaller = (saved / input_size * 100.0) if input_size else 0.0

        for label, value, extra, accent in [
            ("Input", input_name, format_size(input_size), TEXT_PRIMARY),
            ("Output", output_name, format_size(output_size), TEXT_PRIMARY),
            ("Saved", format_size(saved), f"({smaller:.1f}% smaller)", TEXT_SUCCESS),
            ("Time", f"{result['elapsed']:.2f}s", "", TEXT_PRIMARY),
        ]:
            self.results_layout.addWidget(self._result_row(label, value, extra, accent))

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"color: {BORDER}; background: {BORDER}; min-height: 1px;")
        self.results_layout.addWidget(divider)

        title = QLabel("Top 5 most frequent characters")
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px;")
        self.results_layout.addWidget(title)

        top_chars: List[Tuple[str, float]] = result.get("top_chars", [])
        max_pct = max((pct for _, pct in top_chars), default=0.0)
        for char, pct in top_chars:
            self.results_layout.addWidget(FrequencyBar(char, pct, max_pct))

        success = QLabel(f"✓ Compressed → {output_name}")
        success.setStyleSheet(f"color: {TEXT_SUCCESS}; font-size: 12px; font-weight: 500;")
        self.results_layout.addWidget(success)
        self.results_layout.addStretch(1)

    def _result_row(self, label_text: str, value: str, extra: str, value_color: str) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QLabel(label_text)
        label.setFixedWidth(52)
        label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")

        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 12px;")

        extra_label = QLabel(extra)
        extra_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        extra_label.setStyleSheet(f"color: {value_color}; font-size: 12px;")

        layout.addWidget(label)
        layout.addWidget(value_label)
        layout.addStretch(1)
        layout.addWidget(extra_label)
        return row
