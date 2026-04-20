from __future__ import annotations

import heapq
from dataclasses import dataclass
from itertools import count
from typing import Dict, List, Optional, Tuple


@dataclass
class HuffmanNode:
    char: Optional[str]
    freq: int
    left: Optional["HuffmanNode"] = None
    right: Optional["HuffmanNode"] = None

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None


def build_frequency_table(text: str) -> Dict[str, int]:
    freq_table: Dict[str, int] = {}
    for char in text:
        freq_table[char] = freq_table.get(char, 0) + 1
    return freq_table


def build_huffman_tree(freq_table: Dict[str, int]) -> HuffmanNode:
    if not freq_table:
        raise ValueError("File is empty.")

    order = count()
    heap: List[Tuple[int, int, HuffmanNode]] = [
        (freq, next(order), HuffmanNode(char=char, freq=freq))
        for char, freq in freq_table.items()
    ]
    heapq.heapify(heap)

    while len(heap) > 1:
        left_freq, _, left_node = heapq.heappop(heap)
        right_freq, _, right_node = heapq.heappop(heap)
        parent = HuffmanNode(
            char=None,
            freq=left_freq + right_freq,
            left=left_node,
            right=right_node,
        )
        heapq.heappush(heap, (parent.freq, next(order), parent))

    return heap[0][2]


def build_code_table(root: HuffmanNode) -> Dict[str, str]:
    codes: Dict[str, str] = {}

    def visit(node: HuffmanNode, prefix: str) -> None:
        if node.is_leaf:
            codes[node.char or ""] = prefix or "0"
            return
        if node.left is not None:
            visit(node.left, prefix + "0")
        if node.right is not None:
            visit(node.right, prefix + "1")

    visit(root, "")
    return codes


def encode(text: str, code_table: Dict[str, str]) -> str:
    return "".join(code_table[char] for char in text)


def decode(bits: str, root: HuffmanNode) -> str:
    if not bits:
        return ""
    if root.is_leaf:
        return (root.char or "") * len(bits)

    output: List[str] = []
    current = root
    for bit in bits:
        current = current.left if bit == "0" else current.right
        if current is None:
            raise ValueError("Corrupted Huffman data.")
        if current.is_leaf:
            output.append(current.char or "")
            current = root
    return "".join(output)


def top_n_chars(freq_table: Dict[str, int], n: int = 5) -> List[Tuple[str, float]]:
    total = sum(freq_table.values())
    if total == 0:
        return []
    ranked = sorted(freq_table.items(), key=lambda item: (-item[1], item[0]))
    return [
        (char, (count_value / total) * 100.0)
        for char, count_value in ranked[:n]
    ]
