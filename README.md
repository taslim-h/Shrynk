# Shrynk

Lossless text file compression desktop app built with PyQt5 and Huffman coding.

Screenshot: add app screenshot here.

## Requirements

- Python 3.8+
- PyQt5

## Install

```bash
git clone ...
cd shrynk
pip install -e .
```

## Usage

```bash
shrynk
```

## How Huffman Coding Works

Huffman coding is a lossless compression method that assigns shorter binary codes to characters that appear more often and longer codes to characters that appear less often. This reduces the overall number of bits needed to represent a text file while still allowing the original content to be reconstructed exactly during decompression.

## File Format

Shrynk stores compressed files as `.huf` archives. Each file contains a magic header, the original text length, a serialized Huffman tree, the number of valid bits in the final byte, and the packed encoded data so decompression can happen without any external metadata.
