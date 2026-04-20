from __future__ import annotations

import struct
from io import BytesIO
from typing import Tuple

from .huffman import HuffmanNode

LEGACY_MAGIC = b"SHRNK"
MAGIC = b"SHR2K"


def _serialize_tree(node: HuffmanNode) -> bytes:
    buffer = bytearray()

    def visit(current: HuffmanNode) -> None:
        if current.is_leaf:
            char_bytes = (current.char or "").encode("utf-8")
            buffer.extend(b"\x01")
            buffer.extend(struct.pack(">H", len(char_bytes)))
            buffer.extend(char_bytes)
            return
        buffer.extend(b"\x00")
        if current.left is None or current.right is None:
            raise ValueError("Invalid Huffman tree.")
        visit(current.left)
        visit(current.right)

    visit(node)
    return bytes(buffer)


def _deserialize_tree(data: bytes) -> HuffmanNode:
    stream = BytesIO(data)

    def read_node() -> HuffmanNode:
        marker = stream.read(1)
        if not marker:
            raise ValueError("Invalid .huf file.")

        if marker == b"\x01":
            char_length_data = stream.read(2)
            if len(char_length_data) != 2:
                raise ValueError("Invalid .huf file.")
            char_length = struct.unpack(">H", char_length_data)[0]
            char_bytes = stream.read(char_length)
            if len(char_bytes) != char_length:
                raise ValueError("Invalid .huf file.")
            return HuffmanNode(char=char_bytes.decode("utf-8"), freq=0)

        if marker != b"\x00":
            raise ValueError("Invalid .huf file.")

        left = read_node()
        right = read_node()
        return HuffmanNode(char=None, freq=0, left=left, right=right)

    root = read_node()
    if stream.read(1):
        raise ValueError("Invalid .huf file.")
    return root


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
    tree_bytes = _serialize_tree(tree_root)
    packed_bits, valid_bits_last_byte = _pack_bits(encoded_bits)

    with open(output_path, "wb") as handle:
        handle.write(MAGIC)
        handle.write(struct.pack(">I", original_len))
        handle.write(struct.pack(">I", len(tree_bytes)))
        handle.write(tree_bytes)
        handle.write(struct.pack(">B", valid_bits_last_byte))
        handle.write(packed_bits)


def estimate_huf_size(original_len: int, tree_root: HuffmanNode, encoded_bits: str) -> int:
    tree_bytes = _serialize_tree(tree_root)
    packed_bits, _ = _pack_bits(encoded_bits)
    header_size = len(MAGIC) + 4 + 4 + 1
    return header_size + len(tree_bytes) + len(packed_bits)


def read_huf(input_path: str) -> Tuple[int, HuffmanNode, str]:
    with open(input_path, "rb") as handle:
        magic = handle.read(len(MAGIC))
        if magic not in {MAGIC, LEGACY_MAGIC}:
            raise ValueError("Invalid .huf file.")

        original_len = struct.unpack(">I", handle.read(4))[0]
        tree_length = struct.unpack(">I", handle.read(4))[0]
        tree_data = handle.read(tree_length)
        valid_bits_last_byte = struct.unpack(">B", handle.read(1))[0]
        bit_data = handle.read()

    if len(tree_data) != tree_length:
        raise ValueError("Invalid .huf file.")

    if magic == MAGIC:
        try:
            tree_root = _deserialize_tree(tree_data)
        except (UnicodeDecodeError, ValueError) as exc:
            raise ValueError("Invalid .huf file.") from exc
    else:
        try:
            import json

            legacy_tree = json.loads(tree_data.decode("utf-8"))
            tree_root = _deserialize_legacy_tree(legacy_tree)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError("Invalid .huf file.") from exc

    encoded_bits = _unpack_bits(bit_data, valid_bits_last_byte) if bit_data else ""
    return original_len, tree_root, encoded_bits


def _deserialize_legacy_tree(data: object) -> HuffmanNode:
    if not isinstance(data, dict):
        raise ValueError("Invalid .huf file.")
    return HuffmanNode(
        char=data.get("char"),  # type: ignore[arg-type]
        freq=int(data["freq"]),
        left=_deserialize_legacy_tree(data["left"]) if data.get("left") else None,  # type: ignore[arg-type]
        right=_deserialize_legacy_tree(data["right"]) if data.get("right") else None,  # type: ignore[arg-type]
    )
