# Shrynk Builder Handbook

## Preface

This report is written as the version I would want if I had to build the entire Shrynk project again from zero without depending on memory. It explains not only what the project is, but how to think about it, how to design it, how to implement it, what mistakes can happen, and how the final version was improved.

If I had to rebuild this project from scratch, this is the document I would follow like a small book.

## Part 1: Understanding The Project Before Writing Code

### 1. What I Was Trying To Build

The project goal was to build a desktop application that can:

- take a `.txt` file
- compress it using Huffman coding
- save it as a `.huf` file
- later read the `.huf` file
- reconstruct the original text exactly

This means the project is not just “implement Huffman coding.” It is actually four projects combined:

1. algorithm implementation
2. custom file format design
3. GUI app development
4. packaging and deployment on Ubuntu

If I forget that and focus only on the algorithm, I end up with half a project.

### 2. What “Done” Really Means

For this project to be truly complete, the following had to work:

- the algorithm must encode and decode correctly
- the app must not freeze during compression
- the user must be able to select files easily
- the app must show useful feedback
- the compressed file format must contain enough metadata to decode later
- installation must be simple
- the app must launch from terminal and desktop

That is the real checklist.

## Part 2: Planning The Architecture

### 3. Breaking The System Into Modules

A clean way to structure the project is:

- `shrynk/core/huffman.py`
  This should hold the pure compression logic.

- `shrynk/core/fileio.py`
  This should define how the `.huf` file is stored and recovered.

- `shrynk/worker.py`
  This should handle background processing with `QThread`.

- `shrynk/gui/app.py`
  This should build the main window and tab structure.

- `shrynk/gui/compress_tab.py`
  This should implement the compression UI.

- `shrynk/gui/decompress_tab.py`
  This should implement the decompression UI.

- `shrynk/cli.py`
  This should be the packaged launch entrypoint.

That separation matters because it prevents algorithm code from being mixed with UI code.

### 4. Why Huffman Coding Was A Good Choice

Huffman coding is a good project choice because:

- it is classic and academically valid
- it is lossless
- it is implementable in Python
- it has visible results
- it gives a clear bridge between theory and software engineering

The weakness is that it is not always efficient for very small files, because metadata storage adds overhead. That became important later.

## Part 3: Building The Compression Core

### 5. Building The Frequency Table

The first thing needed is a frequency table.

For each character in the input text, count how many times it appears.

Example:

```text
Text: banana

Frequency:
b = 1
a = 3
n = 2
```

This table is the foundation of Huffman coding. Without it, there is no way to decide which characters deserve shorter codes.

### 6. Designing The Huffman Node

I needed a tree node with:

- `char`
- `freq`
- `left`
- `right`

Leaf nodes contain characters. Internal nodes contain no character and only combine frequencies.

The final project uses a `dataclass` called `HuffmanNode`.

### 7. Building The Huffman Tree

To build the tree:

1. create one leaf node per unique character
2. push them into a min-heap by frequency
3. repeatedly pop the two smallest nodes
4. merge them into a parent node
5. push the parent back
6. repeat until one node remains

That final node becomes the root of the tree.

Important implementation detail:

If two nodes have the same frequency, Python still needs a stable way to compare heap items. The project solves that with an increasing counter from `itertools.count()`.

That is the kind of detail that is easy to forget when rebuilding from scratch.

### 8. Building The Code Table

After the tree exists, traverse it:

- left means append `0`
- right means append `1`

When a leaf is reached, store the generated bit string as that character’s code.

Special case:

If the text contains only one unique character, the path would otherwise be empty. The project handles that by assigning `"0"` as the code.

That small edge case is necessary. Without it, single-character files can fail.

### 9. Encoding The Text

Encoding means replacing every character with its Huffman code and concatenating the results into one long bit string.

This is not written to disk directly yet. First, it exists as a Python string of `0` and `1`.

### 10. Decoding The Text

Decoding works by traversing the Huffman tree bit by bit until a leaf node is reached. Then the character is appended to the output and traversal restarts from the root.

If the decoder ever walks into `None`, the input is corrupt.

This is an important validation point.

## Part 4: Designing A Real Compressed File Format

### 11. Why Raw Encoded Bits Are Not Enough

At first glance, it looks like saving the bit string should be enough. It is not.

To decode a compressed file later, I also need:

- the Huffman tree or equivalent codebook
- the original length
- how many bits in the last byte are valid
- a way to recognize that the file is really one of mine

So the file needs metadata.

### 12. The `.huf` Format

The final `.huf` file stores:

- magic header
- original text length
- serialized tree length
- serialized tree bytes
- valid-bit count for the last byte
- packed encoded bytes

This is a proper container format, not just raw compressed bits.

### 13. Packing Bits Into Bytes

The encoded output begins as a bit string like:

```text
101100111010...
```

Files are byte-based, so I must:

1. pad the bit string to a multiple of 8
2. convert each group of 8 bits to one byte
3. record how many bits in the final byte are actually valid

The project implements this in `_pack_bits()` and `_unpack_bits()`.

### 14. The First Big Mistake: JSON Tree Storage

Originally, the tree was stored in JSON. That worked functionally but created a major problem:

- JSON is verbose
- the tree metadata became too large
- many small files became larger after “compression”

This is a classic example of something being logically correct but practically poor.

The final version replaced JSON tree storage with a compact binary serialization:

- internal node marker `0x00`
- leaf marker `0x01`
- leaf character byte length
- UTF-8 bytes of the character

This was a major improvement.

### 15. Legacy Compatibility

Even after moving to the binary format, the reader still supports older legacy `.huf` files created with the JSON-based format.

That means I learned an important software lesson:

when you improve a storage format, think about backward compatibility.

## Part 5: Making The App Practical

### 16. Why Background Workers Were Necessary

If I run compression directly in the main GUI thread, the app freezes while processing.

That is bad desktop behavior.

The solution is `QThread`. The project creates:

- `CompressWorker`
- `DecompressWorker`

These workers:

- perform the heavy work in the background
- emit progress updates
- emit success or error messages back to the GUI

That keeps the interface responsive.

### 17. Compression Worker Logic

The compression worker does the following:

1. read the text file
2. validate that it is not empty
3. build the frequency table
4. build the Huffman tree
5. build the code table
6. encode the text
7. estimate final `.huf` size
8. reject compression if output would be larger
9. write the `.huf` file
10. return result summary

The size-estimation step is critical.

### 18. The Second Big Mistake: Allowing Bad Compression Results

At one point the app would happily produce a `.huf` file even if it was larger than the original.

That is technically not a decoding bug, but it is bad product behavior.

The final version fixes this by using `estimate_huf_size()` before writing. If compression would increase size, the app stops and explains why.

This is one of the best practical improvements in the final system.

### 19. Decompression Worker Logic

The decompression worker:

1. reads the `.huf` file
2. validates the magic header and metadata
3. reconstructs the tree
4. unpacks the encoded bits
5. decodes the original text
6. checks that restored length matches original length
7. writes the `.txt` file

This length check is useful because it catches malformed or corrupted input.

## Part 6: Building The GUI

### 20. Choosing The UI Structure

The app needed two main tasks:

- compression
- decompression

So a tabbed layout made sense.

The final main window contains:

- app header
- `Compress` tab
- `Decompress` tab

Each tab has:

- input file selector
- output settings
- main action button
- progress display
- results card

### 21. Main Window

The main window is built in `shrynk/gui/app.py`.

One interesting part is the custom `EqualWidthTabBar`, which forces the two tabs to divide the available tab width equally. That was added after a layout bug where the tabs remained visually compressed.

### 22. The Third Big Mistake: Fixed Window Size

The early window design used a fixed size that was too restrictive. Once the results panel filled with rows and charts, the layout broke.

This caused:

- clipped content
- visual overlap
- poor resizing behavior

The final version switched to a larger resizable window with a minimum size.

### 23. Compress Tab

The compress tab includes:

- read-only input path field
- browse button
- auto-output checkbox
- optional custom output path
- compress button
- progress label and progress bar
- result summary and top-character frequency bars

The frequency bars help make the algorithm results visible to the user, which is useful in a project demo.

### 24. Decompress Tab

The decompress tab mirrors the compression flow but with simpler results.

It shows:

- input `.huf`
- output `.txt`
- elapsed time
- success message

### 25. Scrollable Results Area

One important improvement was replacing the plain result widget with a scrollable result area using `QScrollArea`.

That solved layout overflow when the result content became tall.

### 26. Styling And Theme

The theme is centralized in `shrynk/gui/theme.py` and the stylesheet is built in `shrynk/cli.py`.

This separation is useful because:

- colors can be changed in one place
- widget styling is consistent
- the UI feels like a single application instead of unrelated widgets

### 27. The Fourth Big Mistake: Leaking Styles

Some parent-level border styles affected child widgets unexpectedly. This created strange lines and unpolished visuals.

The final fix used object-specific selectors such as:

- `#appHeader`
- `#resultsCard`
- `#resultsHeader`
- `#resultsScroll`
- `#resultsBody`

This is a good reminder that broad Qt stylesheet selectors can easily have side effects.

### 28. Checkbox Indicator And Tab Alignment

Two smaller but important polish issues were:

- the checkbox checkmark was not clearly visible
- the tab header widths were not truly 50/50

These were solved by:

- adding `check.svg` and using it for checked state
- creating `EqualWidthTabBar`

Small UI problems matter because they affect perceived quality.

## Part 7: Packaging And Launching

### 29. Why Packaging Matters

Running a Python file manually is not enough for a real app. I needed:

- an installable package
- a stable launch command
- a clean entrypoint

That is the role of `setup.py`.

### 30. The Fifth Big Mistake: Broken Entrypoint

The installed command originally tried to import `main:main`, but `main.py` was not reliably part of the installed package.

That caused:

```text
ModuleNotFoundError: No module named 'main'
```

The fix was:

- move the real entrypoint into `shrynk/cli.py`
- point the console script to `shrynk.cli:main`
- keep `main.py` only as a compatibility wrapper

This is one of the most important lessons in Python packaging from this project.

### 31. Ubuntu Desktop Shortcut

To avoid launching from terminal every time, I also needed a `.desktop` file:

- `Name=Shrynk`
- `Exec=/path/to/.venv/bin/shrynk`
- `Path=/path/to/project`
- `Terminal=false`

Then it can be copied to the Ubuntu Desktop and marked executable.

That turns the project from “developer tool” into “desktop app.”

## Part 8: How I Would Rebuild It From Scratch

### 32. Recommended Build Order

If I had to rebuild this project again, I would follow this exact order:

1. Implement frequency counting
2. Implement Huffman tree construction
3. Implement code generation
4. Implement encode/decode functions
5. Write round-trip tests in a temporary script
6. Design the `.huf` container format
7. Implement pack/unpack bit handling
8. Implement file read/write functions
9. Add size estimation before writing
10. Add worker threads
11. Build the GUI tabs
12. Add progress reporting
13. Add result rendering
14. Add styling
15. Fix packaging and create installable entrypoint
16. Add desktop launcher
17. Write documentation

This order reduces confusion because each layer depends on the previous one.

### 33. What I Should Verify At Each Stage

Before moving to the next stage, I should verify:

After core algorithm:
- encode then decode returns original text

After file format:
- write then read preserves tree and data

After worker layer:
- UI remains responsive during processing

After GUI:
- success and error states render correctly

After packaging:
- installed `shrynk` command launches correctly

After deployment:
- desktop shortcut opens the app

## Part 9: Ubuntu Setup From Zero

### 34. Clean Ubuntu Setup

On a fresh Ubuntu machine, I would do:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
git clone https://github.com/taslim-h/Shrynk.git
cd Shrynk
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
shrynk
```

If PyQt5 causes issues:

```bash
sudo apt install -y python3-pyqt5
```

### 35. Desktop Shortcut Setup

Create or use:

```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Shrynk
Comment=Lossless text file compression
Exec=/absolute/path/to/Shrynk/.venv/bin/shrynk
Path=/absolute/path/to/Shrynk
Terminal=false
Categories=Utility;
```

Then:

```bash
cp Shrynk.desktop ~/Desktop/Shrynk.desktop
chmod +x ~/Desktop/Shrynk.desktop
```

If Ubuntu blocks it at first:

- right-click
- choose `Allow Launching`

## Part 10: What I Learned From This Project

### 36. Algorithm Correctness Is Only One Part

At the start, it is easy to think:

“If Huffman coding works, the project is done.”

That is false.

Real software also needs:

- packaging
- UI
- validation
- error handling
- deployment
- documentation

### 37. Metadata Size Matters

Compression projects are not just about bit savings inside the payload. Metadata can destroy the result if it is not designed carefully.

That is why moving from JSON tree storage to compact binary tree storage mattered so much.

### 38. UX Matters In Academic Projects Too

Even if the algorithm is correct, users notice:

- broken layout
- missing checkmarks
- squeezed tabs
- ugly borders
- no desktop icon

So software quality is broader than algorithm quality.

### 39. Packaging Bugs Can Make A Good App Look Broken

The entrypoint bug was a good reminder that deployment details are part of engineering, not optional polish.

### 40. Documentation Is Part Of The Product

If the app works but installation is unclear, the project still feels incomplete.

The README and these reports matter because they preserve the logic behind the implementation.

## Part 11: Future Expansion Ideas

If I continue this project later, I would consider:

- unit tests for Huffman and file-format logic
- drag-and-drop support
- multiple-file batch processing
- app icon and brand assets
- `.deb` package generation
- compression ratio history
- binary file support
- performance benchmark mode

## Part 12: Final Summary

Shrynk became much more than a Huffman coding demo. It turned into a usable Ubuntu desktop application with:

- a working compression and decompression engine
- a custom file format
- safe handling of bad compression cases
- a responsive GUI
- improved layout and styling
- installable package behavior
- a desktop launcher
- practical documentation

If I had to rebuild it from zero, I would use this exact understanding:

first build the compression core correctly,
then build a valid file format,
then make it responsive,
then make it usable,
then make it installable,
then document everything.

That is the real development path from ground zero to an advanced finished project.
