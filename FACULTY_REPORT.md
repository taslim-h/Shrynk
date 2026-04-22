# Shrynk Project Report

## 1. Project Title

Shrynk: A Desktop Application for Lossless Text File Compression Using Huffman Coding

## 2. Project Overview

Shrynk is a desktop application developed in Python with PyQt5 to perform lossless compression and decompression of text files. The application accepts plain UTF-8 `.txt` files as input, compresses them into a custom `.huf` format using Huffman coding, and restores them back to `.txt` format through decompression.

The project combines algorithm design, desktop GUI development, file-format design, packaging, and Linux deployment into one complete software system. The goal was not only to implement the Huffman algorithm, but also to turn that implementation into a usable end-user desktop product on Ubuntu.

## 3. Objectives

The main objectives of the project were:

- To implement lossless compression using Huffman coding
- To create a graphical desktop interface for compression and decompression
- To design a custom compressed file format for storing encoded data and metadata
- To provide a practical Linux/Ubuntu application that can be launched from both terminal and desktop shortcut
- To handle common user and system errors safely
- To make the project understandable, installable, and maintainable

## 4. Problem Statement

Text files often contain repeated characters and patterns. A naive storage approach uses fixed-length character encodings without considering frequency distribution. Huffman coding addresses this inefficiency by assigning shorter codes to more frequent characters and longer codes to less frequent characters, reducing the total number of bits required for repetitive data.

However, building a real application around this concept requires solving more than the algorithm itself. The project needed:

- a user interface
- asynchronous processing so the GUI does not freeze
- a reliable compressed file format
- output validation
- packaging and execution support on Ubuntu

Shrynk was built to solve that full practical problem.

## 5. Scope

The implemented scope includes:

- Compression of `.txt` files using Huffman coding
- Decompression of `.huf` files back to text
- PyQt5 desktop interface with separate compress and decompress tabs
- Result summaries showing file sizes, timing, and character frequency statistics
- Ubuntu installation instructions and desktop launcher support
- Protection against writing compressed output when compression would increase file size
- Support for reading an older legacy `.huf` format

The project does not currently include:

- compression of binary files
- batch processing of multiple files
- drag-and-drop support
- unit test suite
- Windows or macOS specific packaging

## 6. Technology Stack

The following technologies were used:

- Python: primary programming language
- PyQt5: GUI framework
- setuptools: packaging and console script creation
- Git and GitHub: version control and hosting
- Ubuntu Linux: target development and execution platform

## 7. System Architecture

The project is organized into clear layers:

### 7.1 Entry Layer

- `setup.py` defines the installable application
- `shrynk/cli.py` is the packaged GUI entrypoint
- `main.py` acts as a compatibility wrapper

### 7.2 GUI Layer

- `shrynk/gui/app.py` builds the main application window and tab system
- `shrynk/gui/compress_tab.py` handles compression inputs, progress, and result rendering
- `shrynk/gui/decompress_tab.py` handles decompression inputs, progress, and result rendering
- `shrynk/gui/theme.py` stores visual theme constants

### 7.3 Worker Layer

- `shrynk/worker.py` runs compression and decompression in background threads using `QThread`

### 7.4 Core Algorithm Layer

- `shrynk/core/huffman.py` contains the Huffman tree, code generation, encoding, decoding, and statistics logic
- `shrynk/core/fileio.py` contains the custom `.huf` file format read/write logic

## 8. Functional Flow

### 8.1 Compression Flow

1. User selects a `.txt` file
2. The app validates the input path and output path
3. The compression worker reads the UTF-8 text
4. A frequency table is built
5. A Huffman tree is generated
6. A binary code table is derived from the tree
7. The text is encoded into a bit string
8. The estimated compressed file size is calculated
9. If compression would produce a larger file, the process stops with a message
10. Otherwise, the encoded content and tree are written into a `.huf` file
11. The GUI displays result details

### 8.2 Decompression Flow

1. User selects a `.huf` file
2. The app validates the file and output path
3. The decompression worker reads the custom file
4. The Huffman tree and encoded bitstream are reconstructed
5. The encoded bits are decoded into text
6. The restored text is written to a `.txt` file
7. The GUI displays decompression results

## 9. Huffman Coding Implementation

The core compression logic is implemented in `shrynk/core/huffman.py`.

### 9.1 Frequency Table

The program first counts how often each character appears in the input text. This frequency table determines the code lengths assigned later.

### 9.2 Huffman Tree

Each unique character starts as a leaf node in a priority queue ordered by frequency. The two least frequent nodes are repeatedly merged into a parent node until one root node remains. This produces the Huffman tree.

### 9.3 Code Table

The tree is traversed recursively:

- left edge adds `0`
- right edge adds `1`

The resulting path from root to leaf becomes the code for that character.

### 9.4 Encoding

The text is converted into a long bit string by replacing every character with its Huffman code.

### 9.5 Decoding

During decompression, each bit is used to traverse the tree until a leaf node is reached, reconstructing the original text.

## 10. Custom File Format

Shrynk uses a custom `.huf` format instead of writing raw bits alone. The file must contain enough metadata to decode the text later.

The current format stores:

- magic header
- original text length
- serialized Huffman tree length
- serialized binary Huffman tree
- number of valid bits in the last byte
- packed encoded data

This design supports standalone decompression without any external metadata.

### 10.1 Legacy Format Compatibility

An earlier version of the project stored the Huffman tree as JSON. That format caused significant overhead, especially for small files. The final version uses a more compact binary tree representation while still supporting reading old legacy files.

## 11. Important Design Decisions

### 11.1 Preventing Fake Compression

One practical issue discovered during development was that very small files could become larger after compression because the metadata overhead outweighed the data savings.

To address this, the app estimates the final `.huf` size before writing. If the compressed output would be larger than the original, the app stops and informs the user. This prevents misleading results.

### 11.2 Keeping the GUI Responsive

Compression and decompression are not run directly on the main UI thread. Instead, `QThread` workers handle the heavy work in the background and emit progress signals. This keeps the interface responsive.

### 11.3 Making the App Installable

The project originally had an entrypoint issue caused by the console script pointing at `main.py`, which was not packaged properly. The final design uses `shrynk.cli:main` as the packaged entrypoint, ensuring the app launches correctly after installation.

## 12. User Interface Design

The GUI contains:

- a header with app title and subtitle
- two equal-width tabs: `Compress` and `Decompress`
- file input controls
- optional automatic output-path generation
- progress status and progress bar
- a result card showing output details

The interface was refined during development to solve layout issues such as:

- overlapping result content
- non-scrollable result panels
- compressed tab headers not filling available width
- checkbox indicator visibility
- inconsistent border styling

## 13. File and Module Structure

```text
Shrynk/
├── main.py
├── setup.py
├── README.md
├── Shrynk.desktop
└── shrynk/
    ├── __init__.py
    ├── cli.py
    ├── worker.py
    ├── core/
    │   ├── __init__.py
    │   ├── fileio.py
    │   └── huffman.py
    └── gui/
        ├── __init__.py
        ├── app.py
        ├── compress_tab.py
        ├── decompress_tab.py
        ├── theme.py
        └── assets/
            └── check.svg
```

## 14. Installation and Deployment

The project is designed to run on Ubuntu using a Python virtual environment.

Typical setup:

1. Install Python, `python3-venv`, and `pip`
2. Clone the repository
3. Create `.venv`
4. Activate the environment
5. Run `pip install -e .`
6. Launch with `shrynk`

For easier user access, a `Shrynk.desktop` launcher can be placed on the Ubuntu Desktop and marked executable.

## 15. Validation and Testing

The following forms of validation were performed during development:

- import and packaging verification
- syntax checking with `python -m compileall`
- round-trip compression/decompression tests
- output-size verification
- manual UI testing on Ubuntu

Key issues found and corrected:

- broken installed entrypoint
- excessive metadata overhead from JSON tree storage
- misleading negative compression reporting
- GUI layout overflow and alignment defects

## 16. Challenges Faced

Several practical challenges were encountered:

### 16.1 Packaging Error

The installed `shrynk` launcher failed with `ModuleNotFoundError: No module named 'main'`. This was caused by the script pointing to a top-level file that was not included in the package.

### 16.2 Compression Overhead

Small files sometimes expanded instead of shrinking. The project required redesigning the `.huf` format and adding a preflight size check.

### 16.3 GUI Layout Problems

The initial fixed-size window and non-scrollable results panel caused broken layouts. The window sizing, scroll behavior, and tab rendering had to be redesigned.

### 16.4 Linux Launch Convenience

Users should not need the terminal every time. A desktop launcher was added to improve practical usability on Ubuntu.

## 17. Outcomes

At the end of development, the project achieved the following outcomes:

- a working desktop compression application
- correct lossless decompression
- improved compact file format
- better usability and Ubuntu integration
- clearer documentation for installation and usage

## 18. Limitations

Current limitations include:

- supports only text files, not arbitrary binary files
- no automated unit tests yet
- no installer bundle such as `.deb`
- no performance benchmark suite
- no drag-and-drop or batch folder support

## 19. Future Improvements

Possible future enhancements:

- support for binary files
- unit and integration tests
- drag-and-drop file selection
- batch compression and decompression
- exportable operation logs
- `.deb` package for Ubuntu
- application icon and branding improvements
- compression benchmarking dashboard

## 20. Conclusion

Shrynk demonstrates a complete software project that combines data compression theory with practical application engineering. The project successfully implements Huffman coding, wraps it in a usable desktop GUI, defines a custom compressed file format, handles real-world edge cases, and supports Ubuntu deployment.

The final system is not only an algorithm demonstration, but a usable desktop application that reflects both conceptual understanding and engineering refinement.
