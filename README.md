<a id="top"></a>

# 📦 Invoice Number Barcode Splitter

> Split multi-page PDFs into one PDF per barcode value — with a classic black-and-green terminal look.

> [!IMPORTANT]
> **Your invoices must have a barcode on them.** This program uses barcodes to mark where each document begins and ends. **A barcode starts a new file, and the next barcode ends that file and starts another.** If a scan has no barcodes, nothing is split. See [How Splitting Works](#how-splitting-works).

![Barcode Splitter running on Windows](screenshot.png)

## 📑 Table of Contents

1. [🔖 How Splitting Works (Barcode Demarcation)](#how-splitting-works)
2. [⬇️ Download](#download)
3. [Overview](#overview)
4. [✨ Features](#features)
5. [🖥 Requirements](#requirements)
6. [📚 Dependencies](#dependencies)
7. [🔌 DLL Requirements](#dll-requirements)
8. [⚙️ Configuration](#configuration)
9. [🚀 Usage](#usage)
10. [📦 Building the .exe](#building-the-exe)
11. [🆕 What's New (v2)](#whats-new-v2)
12. [⚠️ Important Notes](#important-notes)
13. [🛠 Troubleshooting](#troubleshooting)

---

<a id="how-splitting-works"></a>

## 🔖 How Splitting Works (Barcode Demarcation)

This program assumes **each invoice has a barcode on it** (usually on its first page). Barcodes are how the program can tell, without a person looking, **where one document in a batch scan stops and the next one starts**.

The program reads the scanned PDF one page at a time, from top to bottom:

1. **A barcode starts a file.** When a page has a barcode, a new output file begins with that page. The file is named after the barcode's value (e.g. `INV-501.pdf`).
2. **Pages without a barcode belong to the current file.** They're added to the file that the last barcode started.
3. **The next barcode ends that file and starts a new one.** The page with the new barcode becomes the first page of the next file.
4. **The last file ends at the last page of the scan.**

```text
Scanned batch.pdf                      Output
─────────────────                      ──────
Page 1  [barcode INV-501]  ──┐
Page 2                       ├──►  INV-501.pdf  (pages 1–2)
                             ┘
Page 3  [barcode INV-502]  ──┐
Page 4                       │
Page 5                       ├──►  INV-502.pdf  (pages 3–5)
                             ┘
Page 6  [barcode INV-503]  ─────►  INV-503.pdf  (page 6)
```

**What this means in practice:**

- ⚠️ **Pages before the first barcode are skipped.** They aren't saved to any output file, so make sure the first page of the scan has a barcode.
- ⚠️ **A scan with no readable barcodes produces no output files**, but the original is still moved to the archive folder (it isn't deleted).
- ⚠️ **If an invoice's barcode can't be read** (missing, smudged, cut off, or too small for the scan resolution), its pages are added to the *previous* invoice's file.
- Only these barcode types count: `CODE128`, `EAN13`, `CODE39`, `I25`. Other codes, such as QR codes, are ignored. If a page has more than one valid barcode, the first one read is used.
- If the **same barcode value shows up more than once in one scan**, all of those sections are combined into a single file.
- If the **same barcode value appears in two different input PDFs on the same run**, the later file overwrites the earlier one in that run's output folder.

<sub>[↑ Back to contents](#-table-of-contents)</sub>

---

<a id="download"></a>

## ⬇️ Download

1. Download **`barcode_splitter-vX.Y.Z-windows-x64.zip`** from the [Releases page](https://github.com/entropytwo-ai/invoice-number-barcode-splitter/releases/latest).
2. Right-click the zip → **Extract All…** (don't run it from inside the zip).
3. Open the extracted `barcode_splitter` folder and double-click **`barcode_splitter.exe`**.

Python, the ZBar DLLs and the Visual C++ runtimes are all bundled in the folder (in `_internal\`), so nothing else needs to be installed. Keep `barcode_splitter.exe` and `_internal\` together; you can put a shortcut to the exe on your desktop.

> Windows SmartScreen may warn about an unsigned app the first time — choose **More info → Run anyway**.

<details>
<summary><b>Why a folder instead of a single .exe? (antivirus false positives)</b></summary>

v2.0.0 shipped as a single-file exe built with PyInstaller's stock bootloader. That bootloader is shared by huge numbers of programs, including real malware, so machine-learning scanners sometimes flag *any* app that contains it. VirusTotal showed 3 of ~70 vendors flagging v2.0.0, which is a typical false positive for PyInstaller apps.

From v2.0.1 the release is built with a bootloader **compiled from source** and in **folder (`--onedir`) mode**, which has no self-extracting payload. Before publishing, the release exe was uploaded to VirusTotal; the link and result are in the release notes.

If your antivirus still quarantines it, report it as a false positive to that vendor (e.g. Microsoft: <https://www.microsoft.com/wdsi/filesubmission>). Code-signing the exe would be the permanent fix.
</details>

<sub>[↑ Back to contents](#-table-of-contents)</sub>

---

<a id="overview"></a>

## Overview

**Barcode Splitter** is a Windows desktop tool that processes every PDF in an input folder, detects barcodes on each page, and splits the pages into separate PDFs grouped by barcode value (e.g. one PDF per invoice number).

Processed input files are archived into dated folders, and archives older than **31 days** are cleaned up automatically.

<sub>[↑ Back to contents](#-table-of-contents)</sub>

---

<a id="features"></a>

## ✨ Features

- **Barcode-based splitting** of multi-page PDFs using `pyzbar` + `PyMuPDF`
- **Supported symbologies:** `CODE128`, `EAN13`, `CODE39`, `I25`
- **Barcode demarcation** — a barcode starts a new file, and the next barcode ends it and starts another ([details](#how-splitting-works))
- **Daily archiving** of processed PDFs into `archive/YYYY-MM-DD/`
- **Automatic retention cleanup** — archive folders older than 31 days are deleted
- **Remembers your folders** — last input/output paths stored in `settings.json`
- **🟩 Terminal-style theme** — black background, bright-green `Courier New` text, green separators
- **Scrollable live log** with a proper scrollbar
- **Status bar** showing the current state (Ready / Processing / Done / Error)
- **Per-file error isolation** — one corrupt PDF no longer aborts the whole batch
- **Thread-safe GUI** — processing runs in a background thread; all UI updates are marshalled to the main thread
- **Run summary** with per-file output counts and page counts for every saved PDF
- Packaged as a **standalone Windows executable** with PyInstaller

<sub>[↑ Back to contents](#-table-of-contents)</sub>

---

<a id="requirements"></a>

## 🖥 Requirements

| Item | Version |
|------|---------|
| OS | Windows 10 or later (64-bit) |
| Python | **3.10.x** (see notes) |

<sub>[↑ Back to contents](#-table-of-contents)</sub>

<a id="dependencies"></a>

## 📚 Dependencies

Install with:

```bash
pip install -r requirements.txt
```

`requirements.txt`:

```
pyzbar==0.1.9
pymupdf
Pillow
pyinstaller
```

<sub>[↑ Back to contents](#-table-of-contents)</sub>

<a id="dll-requirements"></a>

## 🔌 DLL Requirements

`pyzbar` needs the ZBar native libraries on Windows. Both DLLs are included in this repo and must sit **next to the script / executable**:

- `libzbar-64.dll`
- `libiconv.dll`

Source: <https://github.com/NaturalHistoryMuseum/barcode-reader-dlls/releases>

<sub>[↑ Back to contents](#-table-of-contents)</sub>

---

<a id="configuration"></a>

## ⚙️ Configuration

`settings.json` is created automatically in the working directory and stores the last used folders:

```json
{
  "last_input": "C:\\Scans\\Incoming",
  "last_output": "C:\\Scans\\Split"
}
```

If the file is missing or malformed, the app falls back to defaults instead of crashing.

Tunable constants at the top of `barcode_splitter.py`:

| Constant | Default | Purpose |
|----------|---------|---------|
| `DPI` | `400` | Render resolution used for barcode detection |
| `ALLOWED_BARCODE_TYPES` | `CODE128, EAN13, CODE39, I25` | Accepted symbologies |
| `RETENTION_DAYS` | `31` | Archive retention period |
| `BG_COLOR` / `FG_COLOR` | `#000000` / `#00FF00` | Theme colours |
| `FONT_FACE` / `FONT_SIZE` | `Courier New` / `10` | Log font |

<sub>[↑ Back to contents](#-table-of-contents)</sub>

---

<a id="usage"></a>

## 🚀 Usage

1. Run `barcode_splitter.exe` (or `python barcode_splitter.py`).
2. Choose whether to reuse the last **input** folder, or pick a new one.
3. Do the same for the **output** folder.
4. Watch the green-on-black log as each PDF is processed.
5. When finished, a dialog shows where the output was saved.

**Output layout**

```
<output>/
└── 2026-10-28/            # _1, _2 … appended if run more than once a day
    ├── INV-10001.pdf
    └── INV-10002.pdf

<input>/
└── archive/
    └── 2026-10-28/
        └── original_scan.pdf
```

> Pages appearing **before the first barcode** in a PDF are intentionally skipped.

<sub>[↑ Back to contents](#-table-of-contents)</sub>

---

<a id="building-the-exe"></a>

## 📦 Building the .exe

**On Windows** (Python 3.10.x, 64-bit) — just run:

```bat
build.bat
```

which installs `requirements.txt` and runs:

```bat
pyinstaller --clean --noconfirm --onedir --noconsole --name barcode_splitter --version-file version_info.txt ^
  --add-binary "libzbar-64.dll;." --add-binary "libiconv.dll;." ^
  --add-binary "redist\MSVCR120.dll;." --add-binary "redist\MSVCP140.dll;." barcode_splitter.py
```

**On Linux** (cross-build with Wine + Windows Python 3.10 + mingw-w64): `./build_exe_wine.sh`. This also **compiles PyInstaller's bootloader from source** (to avoid antivirus false positives) and creates the release zip.

Output goes to `dist/barcode_splitter/` (the exe plus its `_internal\` folder). Ship the **whole folder** (zipped). Built binaries are git-ignored; releases are published on the Releases page.

> To get the same source-built bootloader on Windows, install Visual Studio Build Tools (C++), then run
> `set PYINSTALLER_COMPILE_BOOTLOADER=1` and `pip install --force-reinstall --no-binary pyinstaller pyinstaller` before `build.bat`.

**Why `redist/`?** `libzbar-64.dll` depends on the Visual C++ 2013 runtime (`MSVCR120.dll`) and PyMuPDF depends on `MSVCP140.dll`. Bundling these Microsoft-signed redistributable DLLs means the exe works on PCs that don't have the VC++ redistributables installed.

<sub>[↑ Back to contents](#-table-of-contents)</sub>

---

<a id="whats-new-v2"></a>

## 🆕 What's New (v2)

**Theming / UI**
- Black background, bright-green Courier New text throughout the window
- Header banner, green separator lines and bottom status bar
- Added a scrollbar to the log area; larger, resizable window

**Bug fixes**
- Removed an unreachable `elif` branch in page accumulation
- Message boxes and log writes are no longer called from the worker thread (Tk is not thread-safe)
- The completion dialog no longer disappears instantly — the app closes after you dismiss it
- One bad PDF no longer kills the batch (per-file `try/except`)
- PDF handles are always closed, even on error, so archiving works on Windows
- `load_config` survives malformed `settings.json`; `save_config` handles write errors
- Graceful message when the input folder has no PDFs
- "Use last folder?" is only asked when a valid last folder exists

**Packaging (v2.0.1)**
- Release is now a zip of the app folder (`--onedir`) built with a from-source PyInstaller bootloader, to stop antivirus false positives on the single-file v2.0.0 exe

**Packaging (v2.0.0 release)**
- Prebuilt `barcode_splitter.exe` published on GitHub Releases
- VC++ runtimes (`MSVCR120.dll`, `MSVCP140.dll`) bundled so the exe runs on clean PCs
- Windows version info embedded (Explorer → Properties → Details)
- One-click `build.bat` and Linux `build_exe_wine.sh` build scripts
- Green-themed scrollbar (native Windows scrollbars ignore colours, so a styled ttk scrollbar is used)
- Log uses ASCII tags (`[OK]`, `[ERR]`, `[ARCH]` …) instead of emoji, which Tk on Windows can't always draw
- Switched from the deprecated `import fitz` to `import pymupdf`

**Code quality**
- Type annotations throughout
- Extracted helpers: `_process_single_pdf()`, `_unique_dest_folder()`, `_ask_folder()`
- PDFs processed in sorted, deterministic order
- Theme constants at the top of the file
- Readable `settings.json` (`indent=2`) and a nicer run summary
- Added `requirements.txt` and `.gitignore`

<sub>[↑ Back to contents](#-table-of-contents)</sub>

---

<a id="important-notes"></a>

## ⚠️ Important Notes

- **Do NOT rename** `libzbar-64.dll` to `zbar.dll` — `pyzbar` looks for the exact name.
- **Use Python 3.10.x.** Python 3.13+ has known `pyzbar` compatibility issues.
- Processing runs in a **background thread**; every GUI update is scheduled on the main thread via `root.after()`.

<sub>[↑ Back to contents](#-table-of-contents)</sub>

---

<a id="troubleshooting"></a>

## 🛠 Troubleshooting

| Problem | Fix |
|---------|-----|
| `Unable to find zbar shared library` / missing `MSVCR120.dll` | When running from source, install Microsoft's *Visual C++ Redistributable for Visual Studio 2013 (x64)* or copy `redist\MSVCR120.dll` next to the script. (The release build already bundles it.) |
| `ImportError: Unable to find zbar shared library` | Make sure `libzbar-64.dll` and `libiconv.dll` are beside the script/exe and not renamed. |
| No barcodes detected | Check scan quality; try raising `DPI`; confirm the symbology is in `ALLOWED_BARCODE_TYPES`. |
| A file shows `0 PDF(s)` in the summary | No valid barcode was found, or the file errored — check the log line marked `[ERR]`. |
| Antivirus / Defender quarantines the exe | False positive from the PyInstaller bootloader; use v2.0.1 or later, or report it to the vendor (see [Download](#download)). |
| `Archive failed` warning | The file is open in another program; close it and re-run. |
| Settings not remembered | Ensure the working directory is writable so `settings.json` can be saved. |
| pyzbar errors on new Python | Downgrade to Python 3.10.x. |

<sub>[↑ Back to contents](#-table-of-contents)</sub>
