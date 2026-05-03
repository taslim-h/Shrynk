# Shrynk — A Complete Guide to the Project
### From Zero to Advanced: Everything You Need to Understand This Codebase

---

## Table of Contents

1. [What Is Shrynk?](#1-what-is-shrynk)
2. [The Big Picture — How It All Fits Together](#2-the-big-picture)
3. [The Theory: What Is Huffman Coding?](#3-the-theory-huffman-coding)
4. [The Core Engine — `huffman.py`](#4-the-core-engine--huffmanpy)
5. [The File Format — `fileio.py`](#5-the-file-format--fileiopy)
6. [The Background Worker — `worker.py`](#6-the-background-worker--workerpy)
7. [The GUI — How the App Looks and Works](#7-the-gui)
8. [The Entry Points — How to Launch the App](#8-the-entry-points)
9. [The Theme System — Colors and Styling](#9-the-theme-system)
10. [The Full Data Flow — Compress and Decompress End-to-End](#10-the-full-data-flow)
11. [The `.huf` Binary File Format — Exact Layout](#11-the-huf-binary-file-format)
12. [Key Design Decisions and Why They Were Made](#12-key-design-decisions)
13. [Limitations and Things You Can Improve](#13-limitations-and-things-you-can-improve)

---

## 1. What Is Shrynk?

Shrynk is a **desktop application** that compresses text files using an algorithm called **Huffman coding**. You give it a `.txt` file, it produces a smaller `.huf` file. You give it a `.huf` file, it perfectly reconstructs the original text.

**It is 100% lossless** — the decompressed output is byte-for-byte identical to the original input. No data is lost.

The project is written entirely in **Python**, and its GUI (Graphical User Interface) is built with **PyQt5** — a library that lets you create desktop windows, buttons, progress bars, and tabs with Python code.

The project structure looks like this:

```
Shrynk-main/
├── main.py              ← The absolute entry point (just calls cli.py)
├── setup.py             ← Packaging config (how to install as a command)
├── shrynk/
│   ├── __init__.py      ← Marks shrynk as a Python package
│   ├── cli.py           ← The launcher: creates the Qt app and window
│   ├── worker.py        ← Background thread for compress/decompress
│   ├── core/
│   │   ├── __init__.py  ← Exports all public functions from core
│   │   ├── huffman.py   ← THE BRAIN: the compression algorithm
│   │   └── fileio.py    ← THE STORAGE: reading/writing .huf files
│   └── gui/
│       ├── __init__.py
│       ├── app.py       ← The main window (title bar + tabs)
│       ├── compress_tab.py   ← The "Compress" tab UI
│       ├── decompress_tab.py ← The "Decompress" tab UI
│       ├── theme.py     ← All color constants
│       └── assets/
│           └── check.svg ← The checkmark icon for checkboxes
```

---

## 2. The Big Picture

Before diving into any code, understand the high-level flow:

**Compression:**
```
your_file.txt
    → Read all characters
    → Count how often each character appears (frequency table)
    → Build a Huffman tree from those frequencies
    → Assign short binary codes to common characters, long codes to rare ones
    → Replace every character in the file with its binary code
    → Pack the binary bits into bytes
    → Write a .huf file containing: [header][the tree][the packed bits]
```

**Decompression:**
```
your_file.huf
    → Read the header (magic bytes, original length)
    → Read and reconstruct the Huffman tree from the file
    → Read the packed bits
    → Unpack bits back to a bit string
    → Walk the Huffman tree bit-by-bit to decode each character
    → Write the recovered text to a .txt file
```

The key insight is that **the tree is stored inside the .huf file**, so decompression never needs the original file — everything needed to decode is self-contained.

---

## 3. The Theory: Huffman Coding

To understand why this works, you need to understand information theory at a basic level.

### 3.1 Why Normal Files Waste Space

When your computer stores text, every character takes exactly **8 bits** (1 byte). The letter `e` takes 8 bits. The letter `q` also takes 8 bits. But `e` appears far more often in English than `q`. This is wasteful — we're giving rare characters the same amount of space as common ones.

### 3.2 The Core Idea

What if we gave **shorter codes to common characters** and **longer codes to rare ones**? The overall file would shrink because most characters would use fewer bits.

For example, imagine a file with these characters:

| Character | Frequency | Fixed (8 bits each) | Huffman code |
|-----------|-----------|---------------------|--------------|
| `e`       | 50        | 8 bits              | `0` (1 bit)  |
| `t`       | 30        | 8 bits              | `10` (2 bits)|
| `a`       | 15        | 8 bits              | `110` (3 bits)|
| `z`       | 5         | 8 bits              | `111` (3 bits)|

Fixed cost: 100 characters × 8 bits = **800 bits**
Huffman cost: (50×1) + (30×2) + (15×3) + (5×3) = 50 + 60 + 45 + 15 = **170 bits**

That's a massive reduction. The more skewed the frequency distribution (some characters very common, others rare), the better Huffman performs.

### 3.3 The Huffman Tree

Huffman coding builds a **binary tree**. Each leaf node holds one character. To find a character's code, you trace the path from the root to that leaf — going left adds a `0`, going right adds a `1`.

**Building the tree — algorithm:**

1. Create one node per unique character, with the character's frequency as its weight.
2. Put all nodes in a **min-heap** (a priority queue sorted by frequency — lowest frequency first).
3. Repeatedly:
   a. Pop the two lowest-frequency nodes.
   b. Create a new internal (parent) node whose frequency = sum of those two.
   c. Make the two nodes children of the parent (lower freq → left, higher → right).
   d. Push the parent back into the heap.
4. When only one node remains in the heap, it's the root of the tree.

**Example:** Characters `a(5)`, `b(9)`, `c(12)`, `d(13)`, `e(16)`, `f(45)`

Step 1: Combine `a(5)` and `b(9)` → internal node `(14)`
Step 2: Combine `(14)` and `c(12)` → internal node `(26)`
...and so on until one root remains.

**The tree guarantees prefix-free codes** — no code is a prefix of any other code. This is critical: it means during decoding, as soon as you reach a leaf, you know that character is complete — you don't need a separator.

### 3.4 Why "Lossless"?

Because decoding perfectly inverts encoding. Given the same tree and the same bit string, you always get back exactly the same text. The tree is stored in the file, so decompression can always reconstruct it.

---

## 4. The Core Engine — `huffman.py`

This file is the mathematical heart of the project. Every function here is pure logic — no file I/O, no GUI, just data transformation.

### 4.1 `HuffmanNode` — The Data Structure

```python
@dataclass
class HuffmanNode:
    char: Optional[str]
    freq: int
    left: Optional["HuffmanNode"] = None
    right: Optional["HuffmanNode"] = None

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None
```

This is a **recursive tree node**. Every node is either:
- A **leaf**: has a `char` (e.g., `'e'`), no children. `is_leaf` returns `True`.
- An **internal node**: has `char=None`, has both `left` and `right` children.

The `@dataclass` decorator auto-generates `__init__`, `__repr__`, and `__eq__` from the fields — it's just a convenience so you don't have to write boilerplate.

### 4.2 `build_frequency_table(text)` — Step 1

```python
def build_frequency_table(text: str) -> Dict[str, int]:
    freq_table: Dict[str, int] = {}
    for char in text:
        freq_table[char] = freq_table.get(char, 0) + 1
    return freq_table
```

Simple character counting. For `"hello"` it returns `{'h':1, 'e':1, 'l':2, 'o':1}`.

`dict.get(key, 0)` returns the current count if the key exists, or `0` if not — avoiding a `KeyError`.

### 4.3 `build_huffman_tree(freq_table)` — Step 2

```python
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
```

**Why the `order = count()` tiebreaker?**

Python's `heapq` compares tuples element by element. If two nodes have the same frequency, it tries to compare the `HuffmanNode` objects — but `HuffmanNode` doesn't define `<`. This would crash. The `order` counter guarantees every tuple's second element is unique, so comparison never falls through to the node object. This is a subtle but important correctness fix.

**`heapq.heapify(heap)`** rearranges the list into a valid min-heap in O(n) time.

**`heapq.heappop`** removes and returns the smallest item (lowest frequency) from the heap.

**`heapq.heappush`** inserts a new item maintaining heap order.

The loop runs until one node remains — that node is the root.

### 4.4 `build_code_table(root)` — Step 3

```python
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
```

This does a **recursive depth-first traversal** of the tree, building up the binary code string as it goes. Every left turn appends `"0"`, every right turn appends `"1"`.

**The edge case `prefix or "0"`**: If the file has only one unique character (e.g., `"aaaa"`), the tree is a single root node with no children. It's already a leaf. The prefix would be `""` (empty string), which is invalid as a code. So we default to `"0"`.

### 4.5 `encode(text, code_table)` — Step 4

```python
def encode(text: str, code_table: Dict[str, str]) -> str:
    return "".join(code_table[char] for char in text)
```

One line. For each character in the text, look up its binary code in the table, concatenate everything. Returns a giant string of `0`s and `1`s like `"01101100110..."`.

### 4.6 `decode(bits, root)` — Decompression Step

```python
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
```

This walks the tree one bit at a time. Start at the root. For each bit: go left (`0`) or right (`1`). When you hit a leaf, you've found a character — record it and jump back to the root. Repeat.

**The single-character edge case**: If `root.is_leaf`, the entire file is made of one repeated character. Every bit in `bits` represents one occurrence of that character. So the decoded text is `root.char * len(bits)`.

### 4.7 `top_n_chars(freq_table, n=5)` — Bonus Statistics

```python
def top_n_chars(freq_table: Dict[str, int], n: int = 5) -> List[Tuple[str, float]]:
    total = sum(freq_table.values())
    if total == 0:
        return []
    ranked = sorted(freq_table.items(), key=lambda item: (-item[1], item[0]))
    return [
        (char, (count_value / total) * 100.0)
        for char, count_value in ranked[:n]
    ]
```

Returns the top 5 most frequent characters with their percentage share. Used by the GUI to show a frequency bar chart after compression. The sort key `-item[1]` sorts by descending frequency, and `item[0]` as a tiebreaker sorts alphabetically.

---

## 5. The File Format — `fileio.py`

This file handles reading and writing the custom `.huf` binary format. It's the bridge between the in-memory Huffman tree and the disk.

### 5.1 Magic Bytes — File Identification

```python
LEGACY_MAGIC = b"SHRNK"
MAGIC = b"SHR2K"
```

The first bytes of every `.huf` file are `SHR2K`. This is called a **magic number** — a signature that identifies the file type. When reading a file, the code checks for this signature first. If it's missing, the file is invalid or corrupted.

`LEGACY_MAGIC = b"SHRNK"` exists because an older version of the format used JSON to store the tree. The reader still supports this old format for backward compatibility.

### 5.2 Tree Serialization — `_serialize_tree(node)`

The Huffman tree is a Python object in memory. To write it to disk, we need to convert it into bytes — this is called **serialization**.

```python
def _serialize_tree(node: HuffmanNode) -> bytes:
    buffer = bytearray()

    def visit(current: HuffmanNode) -> None:
        if current.is_leaf:
            char_bytes = (current.char or "").encode("utf-8")
            buffer.extend(b"\x01")                        # marker: "this is a leaf"
            buffer.extend(struct.pack(">H", len(char_bytes)))  # 2 bytes: char length
            buffer.extend(char_bytes)                     # the character itself
            return
        buffer.extend(b"\x00")                            # marker: "this is an internal node"
        visit(current.left)
        visit(current.right)

    visit(node)
    return bytes(buffer)
```

This is a **preorder traversal** (root → left → right). For each node:
- If internal: write `0x00`, then recurse into left and right children.
- If leaf: write `0x01`, then write the character's byte length (2 bytes, big-endian), then write the character bytes.

**Why store char length?** Because Unicode characters can be 1, 2, 3, or 4 bytes in UTF-8. We need to know how many bytes to read back.

**`struct.pack(">H", n)`** packs integer `n` into 2 bytes in big-endian order. `>` = big-endian, `H` = unsigned short (2 bytes).

### 5.3 Tree Deserialization — `_deserialize_tree(data)`

```python
def _deserialize_tree(data: bytes) -> HuffmanNode:
    stream = BytesIO(data)

    def read_node() -> HuffmanNode:
        marker = stream.read(1)
        if marker == b"\x01":                             # leaf
            char_length = struct.unpack(">H", stream.read(2))[0]
            char_bytes = stream.read(char_length)
            return HuffmanNode(char=char_bytes.decode("utf-8"), freq=0)
        if marker != b"\x00":
            raise ValueError("Invalid .huf file.")
        left = read_node()
        right = read_node()
        return HuffmanNode(char=None, freq=0, left=left, right=right)

    root = read_node()
    if stream.read(1):                                    # ensure nothing is left over
        raise ValueError("Invalid .huf file.")
    return root
```

This is the exact mirror of serialization. It reads the byte stream recursively:
- `0x01` → read char → return a leaf node.
- `0x00` → recursively read left and right children → return an internal node.

`BytesIO` wraps raw bytes in a file-like object so we can call `.read(n)` on it — this makes sequential parsing clean and easy.

### 5.4 Bit Packing — `_pack_bits` and `_unpack_bits`

The encoded bit string (e.g., `"01101100..."`) is a Python string of `'0'`s and `'1'`s. Storing it as text would be wasteful — each character in that string is 8 bits! We need to pack 8 bits of our bit string into each actual byte.

```python
def _pack_bits(encoded_bits: str) -> Tuple[bytes, int]:
    if not encoded_bits:
        return b"", 0

    padding = (-len(encoded_bits)) % 8    # how many 0s to add to make length divisible by 8
    padded = encoded_bits + ("0" * padding)
    chunks = [
        int(padded[index : index + 8], 2)  # convert 8-char binary string to int (0-255)
        for index in range(0, len(padded), 8)
    ]
    valid_bits_last_byte = 8 if padding == 0 else 8 - padding
    return bytes(chunks), valid_bits_last_byte
```

**The padding problem**: If the bit string length isn't a multiple of 8, the last "byte" would be incomplete. We pad with `0`s on the right. But during decompression, we need to know which bits in the last byte are real and which are padding. That's what `valid_bits_last_byte` tracks — it says "only the first N bits of the last byte are real."

**`int("01101100", 2)`** converts a binary string to an integer. That integer becomes one byte.

```python
def _unpack_bits(data: bytes, valid_bits_last_byte: int) -> str:
    bit_string = "".join(f"{byte:08b}" for byte in data)
    if valid_bits_last_byte < 8:
        bit_string = bit_string[: -(8 - valid_bits_last_byte)]  # strip padding bits
    return bit_string
```

**`f"{byte:08b}"`** formats an integer as an 8-character binary string (e.g., `5` → `"00000101"`).

### 5.5 Writing a `.huf` File — `write_huf`

```python
def write_huf(output_path, original_len, tree_root, encoded_bits):
    tree_bytes = _serialize_tree(tree_root)
    packed_bits, valid_bits_last_byte = _pack_bits(encoded_bits)

    with open(output_path, "wb") as handle:
        handle.write(MAGIC)                              # 5 bytes: "SHR2K"
        handle.write(struct.pack(">I", original_len))   # 4 bytes: original char count
        handle.write(struct.pack(">I", len(tree_bytes)))# 4 bytes: tree size
        handle.write(tree_bytes)                        # variable: the tree
        handle.write(struct.pack(">B", valid_bits_last_byte))  # 1 byte: padding info
        handle.write(packed_bits)                       # variable: compressed data
```

`">I"` = big-endian unsigned int (4 bytes). `">B"` = big-endian unsigned byte (1 byte).

### 5.6 Reading a `.huf` File — `read_huf`

```python
def read_huf(input_path):
    with open(input_path, "rb") as handle:
        magic = handle.read(len(MAGIC))
        if magic not in {MAGIC, LEGACY_MAGIC}:
            raise ValueError("Invalid .huf file.")

        original_len = struct.unpack(">I", handle.read(4))[0]
        tree_length = struct.unpack(">I", handle.read(4))[0]
        tree_data = handle.read(tree_length)
        valid_bits_last_byte = struct.unpack(">B", handle.read(1))[0]
        bit_data = handle.read()  # read everything remaining

    # ... deserialize tree, unpack bits, return
```

It reads the file in the exact same order it was written. `handle.read()` with no argument reads all remaining bytes — this gets the packed compressed data.

---

## 6. The Background Worker — `worker.py`

This file connects the algorithm (`huffman.py`, `fileio.py`) to the GUI. It runs the actual compression and decompression work **in a separate thread** so the GUI doesn't freeze.

### 6.1 Why a Separate Thread?

PyQt5 (and all GUI frameworks) run on a single main thread called the **event loop**. This loop is constantly checking for user actions (button clicks, mouse moves) and redrawing the window. If you do heavy computation directly in the main thread, the event loop is blocked — the window freezes, the progress bar won't update, and the app appears crashed.

The solution: run the heavy work in a `QThread`, and communicate progress and results back to the main thread via **signals**.

### 6.2 `CompressWorker`

```python
class CompressWorker(QThread):
    progress = pyqtSignal(int, str)    # emits (percent, status message)
    finished = pyqtSignal(dict)        # emits result dictionary
    error = pyqtSignal(str)            # emits error message

    def __init__(self, input_path, output_path):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path

    def run(self):
        # This method runs in the background thread
        started = time.perf_counter()
        try:
            with open(self.input_path, "r", encoding="utf-8") as handle:
                text = handle.read()
            ...
            self.progress.emit(25, "Analyzing character frequencies...")
            freq_table = build_frequency_table(text)

            self.progress.emit(50, "Building Huffman tree...")
            tree_root = build_huffman_tree(freq_table)
            code_table = build_code_table(tree_root)

            self.progress.emit(85, "Encoding file...")
            encoded_bits = encode(text, code_table)

            # Safety check: would compression actually make the file bigger?
            estimated_output_size = estimate_huf_size(len(text), tree_root, encoded_bits)
            if estimated_output_size >= input_size:
                raise ValueError(f"Compression would increase size ...")

            self.progress.emit(100, "Writing output...")
            write_huf(self.output_path, len(text), tree_root, encoded_bits)

            self.finished.emit({
                "input_size": input_size,
                "output_size": os.path.getsize(self.output_path),
                "elapsed": time.perf_counter() - started,
                "top_chars": top_n_chars(freq_table),
                ...
            })
        except ValueError as exc:
            self.error.emit(str(exc))
        except UnicodeDecodeError:
            self.error.emit("Not a valid text file.")
        ...
```

**`pyqtSignal`** is PyQt5's mechanism for safe cross-thread communication. The worker thread **emits** a signal; the main thread has **slots** (callback functions) connected to those signals. PyQt5 ensures the callback runs on the main thread — making it safe to update UI elements like progress bars.

**`estimate_huf_size`** computes what the output file size would be before actually writing it. Huffman coding can sometimes increase file size for very small or very random files (the tree metadata overhead outweighs the savings). If that's the case, the worker refuses to compress and reports an error instead of creating a larger file.

### 6.3 `DecompressWorker`

```python
class DecompressWorker(QThread):
    def run(self):
        self.progress.emit(40, "Reading Huffman tree...")
        original_len, tree_root, encoded_bits = read_huf(self.input_path)

        self.progress.emit(85, "Decoding file...")
        text = decode(encoded_bits, tree_root)

        # Integrity check: decoded length should match stored original length
        if original_len and len(text) != original_len:
            raise ValueError("Invalid .huf file.")

        self.progress.emit(100, "Writing output...")
        Path(self.output_path).write_text(text, encoding="utf-8")
        ...
```

The integrity check (`len(text) != original_len`) is a sanity check for file corruption. The original character count is stored in the file header. If the decoded text has a different length, something went wrong — either the file is corrupted or truncated.

### 6.4 `format_size` — Human-Readable File Sizes

```python
def format_size(n_bytes: int) -> str:
    if n_bytes < 1024:
        return f"{n_bytes} B"
    if n_bytes < 1024 ** 2:
        return f"{n_bytes / 1024:.2f} KB"
    return f"{n_bytes / (1024 ** 2):.2f} MB"
```

Simple utility. Converts raw byte counts to human-readable strings: `1536` → `"1.50 KB"`.

---

## 7. The GUI

The GUI is structured as a hierarchy of Python classes. Understanding this hierarchy is the key to navigating the GUI code.

```
ShrynkWindow  (app.py)   — The main window, title bar, and tab container
├── CompressTab  (compress_tab.py)  — Everything in the "Compress" tab
└── DecompressTab (decompress_tab.py) — Everything in the "Decompress" tab
```

### 7.1 `ShrynkWindow` — The Main Window (`app.py`)

```python
class ShrynkWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shrynk")
        self.resize(640, 760)
        self.setMinimumSize(560, 680)
        ...
        tabs = QTabWidget()
        tabs.setTabBar(EqualWidthTabBar())
        tabs.addTab(CompressTab(), "Compress")
        tabs.addTab(DecompressTab(), "Decompress")
```

`QMainWindow` is PyQt5's base class for a full application window. `QTabWidget` creates the tabbed interface. Each tab is an instance of `CompressTab` or `DecompressTab`.

**`EqualWidthTabBar`** is a custom subclass of `QTabBar` that overrides `tabSizeHint` to make both tabs equally wide (splitting the available width 50/50). Without this, tabs would be sized based on their label text length.

**`_center_on_screen`** moves the window to the center of the user's monitor on startup.

### 7.2 `CompressTab` — The Compression Tab (`compress_tab.py`)

This is the most complex UI component. It manages:

- **Input file section**: A read-only `QLineEdit` showing the selected file path, plus a "Browse" button.
- **Output file section**: A checkbox for "Auto" mode (same folder, `.huf` extension). If unchecked, shows a custom output path picker.
- **Compress button**: Disabled during compression to prevent double-clicks.
- **Progress section**: A progress bar and label that animate during compression.
- **Results section**: A scrollable area that shows compression results or error messages.

**The auto-output path logic:**

```python
def _auto_output_path(self, input_path: str) -> str:
    return str(Path(input_path).with_suffix(".huf"))
```

`Path("folder/myfile.txt").with_suffix(".huf")` returns `Path("folder/myfile.huf")` — it replaces the extension while keeping the rest of the path intact.

**The animated progress bar:**

```python
def _set_progress(self, percent: int, label: str) -> None:
    animation = QPropertyAnimation(self.progress_bar, b"value", self)
    animation.setDuration(180)
    animation.setStartValue(self.progress_bar.value())
    animation.setEndValue(percent)
    animation.setEasingCurve(QEasingCurve.OutCubic)
    animation.start()
    self._progress_animation = animation
```

`QPropertyAnimation` smoothly animates a Qt property from one value to another. Here it animates the progress bar's `value` property from its current position to the new percent over 180 milliseconds, with an `OutCubic` easing curve (fast start, smooth end).

The reference is stored in `self._progress_animation` — this is important! If it weren't stored, Python's garbage collector would immediately delete the animation object and it would never play.

**`FrequencyBar`** is a custom widget that draws a horizontal bar chart row for a single character's frequency. It contains a character label, a colored bar (whose width is proportional to the frequency percentage), and a percentage label.

**The `_render_success` method** populates the results card after compression with file names, sizes, savings, time elapsed, and the frequency chart.

**Overwrite confirmation:**

```python
def _confirm_overwrite(self, output_path: str) -> bool:
    box = QMessageBox(self)
    box.addButton("Cancel", QMessageBox.RejectRole)
    overwrite_button = box.addButton("Overwrite", QMessageBox.AcceptRole)
    box.exec_()
    return box.clickedButton() is overwrite_button
```

Shows a blocking dialog asking the user if they want to overwrite an existing file. `box.exec_()` blocks until the user clicks a button. `box.clickedButton() is overwrite_button` checks if the user clicked "Overwrite" specifically.

### 7.3 `DecompressTab` — The Decompression Tab (`decompress_tab.py`)

Structurally identical to `CompressTab` but simpler — it doesn't show frequency bars in the results (there's no frequency table during decompression, only during compression). It uses `DecompressWorker` instead of `CompressWorker`.

The auto-output path logic here replaces `.huf` with `.txt`:
```python
def _auto_output_path(self, input_path: str) -> str:
    return str(Path(input_path).with_suffix(".txt"))
```

---

## 8. The Entry Points

### 8.1 `main.py` — The Absolute Root

```python
from shrynk.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
```

Three lines. Imports `main` from `cli.py` and calls it. `raise SystemExit(main())` passes the return code to the OS (0 = success). This file exists so you can run the app with `python main.py`.

### 8.2 `cli.py` — The Real Launcher

This file does the actual work of creating the Qt application. It:

1. Imports all color constants from `theme.py`.
2. Defines `build_stylesheet()` — a function that returns a giant CSS-like string that styles the entire application (all `QWidget`, `QPushButton`, `QProgressBar`, etc. rules).
3. Defines `main()` which creates `QApplication`, applies the stylesheet, creates `ShrynkWindow`, shows it, and starts the event loop.

The stylesheet uses Python f-strings with the color constants from `theme.py`, so all colors flow from one place.

**The checkbox check.svg path trick:**

```python
check_icon = (Path(__file__).resolve().parent / "gui" / "assets" / "check.svg").as_posix()
```

`__file__` is the path to `cli.py` itself. `.resolve().parent` is the directory containing it (`shrynk/`). Then we navigate to `gui/assets/check.svg`. `.as_posix()` converts backslashes to forward slashes for cross-platform Qt compatibility.

### 8.3 `setup.py` — Installation

```python
setup(
    name="shrynk",
    entry_points={
        "console_scripts": [
            "shrynk=shrynk.cli:main",
        ],
    },
    install_requires=["PyQt5"],
)
```

`console_scripts` tells `pip` to create a command-line shortcut. After `pip install -e .`, you can type `shrynk` in the terminal and it runs `shrynk.cli:main` directly — the same as `python main.py`.

---

## 9. The Theme System

`theme.py` is the single source of truth for all colors:

```python
BG_WINDOW   = "#1E1E1E"   # Very dark gray — the window background
BG_SURFACE  = "#252525"   # Slightly lighter — cards and panels
BG_INPUT    = "#2A2A2A"   # Even lighter — input fields
BG_BUTTON   = "#303030"   # Button background
BG_PRIMARY  = "#2D6BE4"   # Blue — the main "Compress" button
BG_PRIMARY_HVR = "#3D7BF4" # Slightly lighter blue — hover state

TEXT_PRIMARY   = "#E8E8E8"  # Near-white — main text
TEXT_SECONDARY = "#888888"  # Gray — labels, subtitles
TEXT_SUCCESS   = "#66BB6A"  # Green — success messages, savings
TEXT_ERROR     = "#EF5350"  # Red — error messages
TEXT_ACCENT    = "#4D8AFF"  # Blue — the icon, focus border, percentage bar

BORDER         = "#383838"  # Dark border between elements
TAB_ACTIVE_LINE = "#4D8AFF" # Blue underline on the selected tab
```

This is a **dark theme** palette. The design avoids pure black (`#000000`) to reduce eye strain — the darkest background is `#1E1E1E`. There are three levels of "surface" depth (window → surface → input → button) creating visual layering.

---

## 10. The Full Data Flow

Let's trace a complete compression from button click to file on disk.

**User clicks "Compress":**

1. `CompressTab.start_compression()` is called.
2. Input path is validated (file exists, is `.txt`, is non-empty, output is writable).
3. If output file already exists, confirmation dialog shown.
4. `compress_button.setDisabled(True)` — prevents double-click.
5. A `CompressWorker` is instantiated with `input_path` and `output_path`.
6. Worker's `progress` signal is connected to `_set_progress` (updates the progress bar).
7. Worker's `finished` signal is connected to `_on_success` (renders results).
8. Worker's `error` signal is connected to `_on_error` (shows error).
9. `worker.start()` — launches the background thread, calling `worker.run()`.

**Inside `CompressWorker.run()` (background thread):**

10. Read the file as UTF-8 text.
11. Emit `progress(25, "Analyzing...")` → progress bar animates to 25%.
12. `build_frequency_table(text)` → `{'e': 1502, 't': 1187, ...}`
13. Emit `progress(50, "Building tree...")`  → animates to 50%.
14. `build_huffman_tree(freq_table)` → builds the tree in the heap.
15. `build_code_table(root)` → `{'e': '00', 't': '01', 'a': '100', ...}`
16. Emit `progress(85, "Encoding...")` → animates to 85%.
17. `encode(text, code_table)` → giant bit string.
18. `estimate_huf_size(...)` → check if it's worth saving.
19. Emit `progress(100, "Writing...")`.
20. `write_huf(output_path, ...)` → writes the binary file.
21. Emit `finished({...})` → signals the main thread.

**Back in the main thread:**

22. `_on_success(result)` is called via the signal.
23. `compress_button.setDisabled(False)` — re-enables the button.
24. `_render_success(result)` fills the results card with stats and frequency bars.

**Decompression flow is the mirror:**

1. Click "Decompress" → `DecompressTab.start_decompression()`.
2. Validates `.huf` input.
3. Spawns `DecompressWorker`.
4. Worker calls `read_huf()` → gets `(original_len, tree_root, encoded_bits)`.
5. Worker calls `decode(encoded_bits, tree_root)` → recovers text.
6. Integrity check: `len(text) == original_len`.
7. Writes text to `.txt` file.
8. Emits `finished({...})`.
9. Results card shows input/output sizes and time.

---

## 11. The `.huf` Binary File Format — Exact Layout

Every `.huf` file has this exact byte layout:

```
Offset    Size       Content
──────────────────────────────────────────────────────────
0         5 bytes    Magic: b"SHR2K" (ASCII)
5         4 bytes    Original text length in chars (big-endian uint32)
9         4 bytes    Tree data size in bytes (big-endian uint32)
13        N bytes    Serialized Huffman tree (variable length)
13+N      1 byte     Valid bits in last byte (1–8, big-endian uint8)
14+N      M bytes    Packed compressed bit data (variable length)
```

**Example:** A file with 1000 characters, 50-byte tree, 750 bytes of compressed data:
- `SHR2K` (5 bytes)
- `00 00 03 E8` (4 bytes = 1000 in big-endian)
- `00 00 00 32` (4 bytes = 50 in big-endian)
- `...50 bytes of tree data...`
- `08` (1 byte = all 8 bits of last byte are valid)
- `...750 bytes of compressed data...`

Total: 5 + 4 + 4 + 50 + 1 + 750 = **814 bytes** to store 1000 characters (which would normally be 1000 bytes).

---

## 12. Key Design Decisions

**Why a custom binary format instead of JSON?**
The earlier `LEGACY_MAGIC = b"SHRNK"` version stored the tree as JSON text. JSON is human-readable but much larger. The binary format uses a compact preorder encoding that's an order of magnitude smaller for the tree.

**Why `QThread` instead of Python's `threading.Thread`?**
`QThread` integrates with PyQt5's signal/slot system, making cross-thread UI updates safe. Python threads can't directly update Qt widgets — you'd need manual synchronization. `QThread` + `pyqtSignal` gives you that for free.

**Why store `original_len` in the header?**
The decoded character count is used as an integrity check. If the number of decoded characters doesn't match what was stored at compression time, the file is corrupted. This catches bit-flip errors, truncated files, and format mismatches.

**Why check if compression increases size?**
Huffman coding has overhead: the tree itself must be stored. For very small files (a few characters) or files with very uniform character distributions (like a file of random bytes), the tree overhead can outweigh the compression savings. The worker detects this and rejects the operation with a clear error message.

**Why use `count()` as a heap tiebreaker?**
`heapq` compares tuple elements in order. If two nodes have equal frequency, Python tries to compare the `HuffmanNode` objects. Since `HuffmanNode` doesn't define `__lt__`, this would raise a `TypeError`. The `count()` iterator provides a unique integer for each node, so comparison always resolves before reaching the node object.

---

## 13. Limitations and Things You Can Improve

**1. Text-only compression**
Shrynk currently only accepts `.txt` files. It reads with `encoding="utf-8"`. Binary files (images, executables) would fail with `UnicodeDecodeError`. You could extend it to handle any file by reading in binary mode and encoding each byte (0–255) as a symbol.

**2. No streaming / large file support**
The entire file is read into memory at once (`text = handle.read()`). A 500MB text file would require ~500MB of RAM plus the encoded bit string (~62MB assuming 50% compression). For huge files, you'd need a chunked streaming approach.

**3. Compression ratio depends on file content**
Huffman coding achieves the best results on files with highly skewed character distributions (natural language works well). Random or already-compressed files (like a `.zip`) will see little or no benefit.

**4. No progress for very fast files**
The progress bar jumps to 85% almost instantly for small files because the computation is faster than the animation duration. This is cosmetic — functionally it's fine.

**5. The CLI entry point only launches the GUI**
`shrynk=shrynk.cli:main` opens the window. There is no command-line mode (e.g., `shrynk compress file.txt`). Adding argparse to `cli.py` could give it a command-line interface that delegates to the core functions in `huffman.py` and `fileio.py` directly, without the GUI.

**6. No multithreading for encoding**
The `encode()` function is a single loop. For very large files, you could split the text into chunks, encode each chunk in a thread pool, and concatenate results. However, Huffman trees built on the whole file can't be trivially parallelized (the tree must be global), so this would require architectural changes.

---

*This report was generated from a complete reading of every source file in the Shrynk-main repository. Every code quote is directly from the actual source.*
