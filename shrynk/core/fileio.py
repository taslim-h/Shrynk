from __future__ import annotations

import json
import struct
from typing import Dict, Tuple

from .huffman import HuffmanNode

MAGIC = b"SHRNK"


def _serialize_tree(node: HuffmanNode) -> Dict[str, object]:
    return {
        "char": node.char,
        "freq": node.freq,
        "left": _serialize_tree(node.left) if node.left else None,
        "right": _serialize_tree(node.right) if node.right else None,
    }


def _deserialize_tree(data: Dict[str, object]) -> HuffmanNode:
    return HuffmanNode(
        char=data.get("char"),  # type: ignore[arg-type]
        freq=int(data["freq"]),
        left=_deserialize_tree(data["left"]) if data.get("left") else None,  # type: ignore[arg-type]
        right=_deserialize_tree(data["right"]) if data.get("right") else None,  # type: ignore[arg-type]
    )


def _pack_bits(encoded_bits: str) -> Tuple[bytes, int]:
    if not encoded_bits:
        return b"", 0

    padding = (-len(encoded_bits)) % 8
    padded = encoded_bits + ("0" * padding)
    chunks = [
        int(padded[index : index + 8], 2)
        for index in range(0, len(padded), 8)
    ]
    valid_bits_last_byte = 8 if padding == 0 else 8 - padding
    return bytes(chunks), valid_bits_last_byte


def _unpack_bits(data: bytes, valid_bits_last_byte: int) -> str:
    if not data:
        return ""

    if valid_bits_last_byte < 1 or valid_bits_last_byte > 8:
        raise ValueError("Invalid compressed file.")

    bit_string = "".join(f"{byte:08b}" for byte in data)
    if valid_bits_last_byte < 8:
        bit_string = bit_string[: -(8 - valid_bits_last_byte)]
    return bit_string


def write_huf(
    output_path: str,
    original_len: int,
    tree_root: HuffmanNode,
    encoded_bits: str,
) -> None:
    tree_bytes = json.dumps(_serialize_tree(tree_root), separators=(",", ":")).encode(
        "utf-8"
    )
    packed_bits, valid_bits_last_byte = _pack_bits(encoded_bits)

    with open(output_path, "wb") as handle:
        handle.write(MAGIC)
        handle.write(struct.pack(">I", original_len))
        handle.write(struct.pack(">I", len(tree_bytes)))
        handle.write(tree_bytes)
        handle.write(struct.pack(">B", valid_bits_last_byte))
        handle.write(packed_bits)


def read_huf(input_path: str) -> Tuple[int, HuffmanNode, str]:
    with open(input_path, "rb") as handle:
        magic = handle.read(len(MAGIC))
        if magic != MAGIC:
            raise ValueError("Invalid .huf file.")

        original_len = struct.unpack(">I", handle.read(4))[0]
        tree_length = struct.unpack(">I", handle.read(4))[0]
        tree_data = handle.read(tree_length)
        valid_bits_last_byte = struct.unpack(">B", handle.read(1))[0]
        bit_data = handle.read()

    try:
        tree_root = _deserialize_tree(json.loads(tree_data.decode("utf-8")))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError("Invalid .huf file.") from exc

    encoded_bits = _unpack_bits(bit_data, valid_bits_last_byte) if bit_data else ""
    return original_len, tree_root, encoded_bits
