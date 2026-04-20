# Shrynk

Shrynk is a PyQt5 desktop app for lossless text file compression and decompression using Huffman coding on Ubuntu/Linux.

It provides:
- Text file compression from `.txt` to `.huf`
- `.huf` decompression back to `.txt`
- Progress feedback and result summaries
- Automatic output path handling
- A desktop launcher on Ubuntu when you create a `.desktop` shortcut

## Features

- Lossless compression for UTF-8 text files
- Desktop GUI built with PyQt5
- Compact binary `.huf` container format
- Backward-compatible reading for older legacy `.huf` files created by earlier versions
- Safety check that refuses compression when the output would be larger than the original file

## Requirements

- Ubuntu 22.04 or newer recommended
- Python 3.10+ recommended
- `python3-venv`
- `pip`

## Install On Ubuntu

### 1. Install system packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

If PyQt5 is missing during setup on your machine, install it with:

```bash
sudo apt install -y python3-pyqt5
```

This project also installs `PyQt5` through `pip` inside the virtual environment, so the system package is usually not required, but it can help on some Ubuntu setups.

### 2. Clone the repository

```bash
git clone https://github.com/taslim-h/Shrynk.git
cd Shrynk
```

### 3. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install the app

```bash
pip install --upgrade pip
pip install -e .
```

This installs the `shrynk` launcher into `.venv/bin/shrynk`.

## Run The App

After activating the virtual environment:

```bash
shrynk
```

You can also launch it directly with:

```bash
.venv/bin/shrynk
```

## Create A Desktop Shortcut On Ubuntu

If you want to start Shrynk without opening a terminal, create a desktop launcher.

Example `Shrynk.desktop`:

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

Then copy it to your Desktop and make it executable:

```bash
cp Shrynk.desktop ~/Desktop/Shrynk.desktop
chmod +x ~/Desktop/Shrynk.desktop
```

On Ubuntu, if the launcher is blocked the first time, right-click it and choose `Allow Launching`.

## How To Use

### Compress a file

1. Open Shrynk.
2. Stay on the `Compress` tab.
3. Click `Browse` and select a `.txt` file.
4. Leave `Auto — same folder, rename to .huf` enabled, or disable it and choose a custom output path.
5. Click `Compress`.
6. Wait for the result panel to show the output file, size summary, elapsed time, and character-frequency statistics.

### Decompress a file

1. Open Shrynk.
2. Switch to the `Decompress` tab.
3. Click `Browse` and select a `.huf` file.
4. Leave `Auto — same folder, rename to .txt` enabled, or choose a custom output path.
5. Click `Decompress`.
6. Wait for the result panel to confirm the restored `.txt` file.

## Important Compression Behavior

Shrynk compresses text with Huffman coding, but very small or low-redundancy files are not always worth compressing.

Because the compressed file must also store metadata needed for decompression, some inputs would become larger if written as `.huf`. Shrynk now detects that before writing and stops with a clear message instead of generating a larger output file.

That means:
- Large repetitive text files usually compress well
- Small files may not compress well
- Some files may be rejected because compression would increase the final size

## Supported Files

- Input for compression: `.txt`
- Output from compression: `.huf`
- Input for decompression: `.huf`
- Output from decompression: `.txt`

Files are read and written as UTF-8 text.

## Project Structure

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
    │   ├── fileio.py
    │   └── huffman.py
    └── gui/
        ├── app.py
        ├── compress_tab.py
        ├── decompress_tab.py
        ├── theme.py
        └── assets/
```

## Development

Activate the virtual environment first:

```bash
source .venv/bin/activate
```

Reinstall editable dependencies after packaging changes:

```bash
pip install -e .
```

Run a quick syntax check:

```bash
python -m compileall shrynk main.py
```

## Troubleshooting

### `ModuleNotFoundError: No module named 'main'`

Reinstall the package:

```bash
pip install -e .
```

This project now uses the packaged CLI entrypoint at `shrynk.cli:main`.

### Desktop icon does not open

- Verify the `Exec=` path in `Shrynk.desktop`
- Make sure the file is executable:

```bash
chmod +x ~/Desktop/Shrynk.desktop
```

- On Ubuntu, right-click the launcher and choose `Allow Launching`

### PyQt5 installation problems

Inside the virtual environment:

```bash
pip install PyQt5
```

If needed on Ubuntu:

```bash
sudo apt install -y python3-pyqt5
```

## How Huffman Coding Works

Huffman coding is a lossless compression method that assigns shorter binary codes to characters that appear more frequently and longer binary codes to characters that appear less frequently. This reduces the total number of bits needed to represent repetitive text while preserving the original data exactly.

## File Format

Shrynk stores compressed files as `.huf` archives.

The current format includes:
- A magic header
- The original text length
- A compact binary-serialized Huffman tree
- The number of valid bits in the last byte
- The packed encoded bitstream

The app can also read older legacy `.huf` files that stored the tree in JSON.

## License

Add a license file if you plan to publish or distribute the project.
