from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Dict

from PyQt5.QtCore import QThread, pyqtSignal

from shrynk.core.fileio import read_huf, write_huf
from shrynk.core.huffman import (
    build_code_table,
    build_frequency_table,
    build_huffman_tree,
    decode,
    encode,
    top_n_chars,
)


def format_size(n_bytes: int) -> str:
    if n_bytes < 1024:
        return f"{n_bytes} B"
    if n_bytes < 1024 ** 2:
        return f"{n_bytes / 1024:.2f} KB"
    return f"{n_bytes / (1024 ** 2):.2f} MB"


class CompressWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, input_path: str, output_path: str) -> None:
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path

    def run(self) -> None:
        started = time.perf_counter()
        try:
            with open(self.input_path, "r", encoding="utf-8") as handle:
                text = handle.read()

            if not text:
                raise ValueError("File is empty.")

            self.progress.emit(25, "Analyzing character frequencies...")
            freq_table = build_frequency_table(text)

            self.progress.emit(50, "Building Huffman tree...")
            tree_root = build_huffman_tree(freq_table)
            code_table = build_code_table(tree_root)

            self.progress.emit(85, "Encoding file...")
            encoded_bits = encode(text, code_table)

            self.progress.emit(100, "Writing output...")
            write_huf(self.output_path, len(text), tree_root, encoded_bits)

            self.finished.emit(
                {
                    "input_path": self.input_path,
                    "output_path": self.output_path,
                    "input_size": os.path.getsize(self.input_path),
                    "output_size": os.path.getsize(self.output_path),
                    "elapsed": time.perf_counter() - started,
                    "top_chars": top_n_chars(freq_table),
                }
            )
        except UnicodeDecodeError:
            self.error.emit("Not a valid text file.")
        except PermissionError:
            self.error.emit("Output location is not writable.")
        except ValueError as exc:
            self.error.emit(str(exc))
        except Exception:
            self.error.emit("Compression failed.")


class DecompressWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, input_path: str, output_path: str) -> None:
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path

    def run(self) -> None:
        started = time.perf_counter()
        try:
            self.progress.emit(40, "Reading Huffman tree...")
            original_len, tree_root, encoded_bits = read_huf(self.input_path)

            self.progress.emit(85, "Decoding file...")
            text = decode(encoded_bits, tree_root)
            if original_len and len(text) != original_len:
                raise ValueError("Invalid .huf file.")

            self.progress.emit(100, "Writing output...")
            Path(self.output_path).write_text(text, encoding="utf-8")

            self.finished.emit(
                {
                    "input_path": self.input_path,
                    "output_path": self.output_path,
                    "input_size": os.path.getsize(self.input_path),
                    "output_size": os.path.getsize(self.output_path),
                    "elapsed": time.perf_counter() - started,
                }
            )
        except PermissionError:
            self.error.emit("Output location is not writable.")
        except ValueError as exc:
            self.error.emit(str(exc))
        except Exception:
            self.error.emit("Decompression failed.")
