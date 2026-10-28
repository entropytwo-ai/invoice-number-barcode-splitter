"""
Barcode Splitter
----------------
Scans a folder of PDFs for barcodes and splits each PDF into separate
output PDFs, one per unique barcode value found.  Processed source files
are archived automatically; archives older than RETENTION_DAYS are deleted.

Theme: black background, bright-green text (Courier New) in the tkinter
       progress window, matching the look of a classic terminal.
"""

import os
import sys
import json
import shutil
import ctypes
import datetime
import threading
from pathlib import Path

import fitz  # PyMuPDF
import tkinter as tk
from tkinter import filedialog, messagebox
from pyzbar.pyzbar import decode
from PIL import Image

# ── Configuration ─────────────────────────────────────────────────────────────
DPI                    = 400
ALLOWED_FILENAME_CHARS = "._-"
ALLOWED_BARCODE_TYPES  = {"CODE128", "EAN13", "CODE39", "I25"}
CONFIG_FILE            = "settings.json"
ARCHIVE_FOLDER_NAME    = "archive"
RETENTION_DAYS         = 31

# ── Theme ─────────────────────────────────────────────────────────────────────
BG_COLOR  = "#000000"    # black background
FG_COLOR  = "#00FF00"    # bright green foreground
FONT_FACE = "Courier New"
FONT_SIZE = 10
# ─────────────────────────────────────────────────────────────────────────────


def enable_windows_ansi() -> None:
    """Enable ANSI escape sequences on Windows 10+ console (no-op elsewhere)."""
    if sys.platform == "win32":
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass


# ── Stdout redirect ───────────────────────────────────────────────────────────

class StdoutRedirector:
    """
    Redirect stdout writes to a Tkinter Text widget.

    Tk widgets must only be touched from the main (GUI) thread, so writes
    coming from the background worker are marshalled via ``after(0, ...)``.
    """

    def __init__(self, text_widget: tk.Text) -> None:
        self.text_widget = text_widget
        self._main_thread = threading.main_thread()

    def _append(self, text: str) -> None:
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tk.END, text)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state="disabled")

    def write(self, text: str) -> None:
        if threading.current_thread() is self._main_thread:
            self._append(text)
        else:
            self.text_widget.after(0, self._append, text)

    def flush(self) -> None:
        pass  # Required for file-like interface


# ── Config persistence ────────────────────────────────────────────────────────

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass  # Fall through to default
    return {"last_input": "", "last_output": ""}


def save_config(config: dict) -> None:
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except OSError as exc:
        print(f"⚠️  Could not save settings: {exc}")


# ── File utilities ────────────────────────────────────────────────────────────

def choose_directory(title: str, initialdir: str) -> str:
    return filedialog.askdirectory(title=title, initialdir=initialdir or os.getcwd())


def sanitize_filename(name: str) -> str:
    """Replace characters that are unsafe for filenames with underscores."""
    return "".join(
        c if c.isalnum() or c in ALLOWED_FILENAME_CHARS else "_"
        for c in name
    )


def save_pdf(pages: list, out_path: Path) -> None:
    """Write a list of fitz.Page objects to a new PDF file."""
    new_doc = fitz.open()
    for p in pages:
        new_doc.insert_pdf(p.parent, from_page=p.number, to_page=p.number)
    new_doc.save(str(out_path))
    new_doc.close()


def move_to_archive(pdf_path: Path, input_folder: Path) -> None:
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    archive_path = input_folder / ARCHIVE_FOLDER_NAME / today
    archive_path.mkdir(parents=True, exist_ok=True)
    target_path = archive_path / pdf_path.name
    try:
        shutil.move(str(pdf_path), str(target_path))
        print(f"    🗂  Archived → {target_path}")
    except OSError as exc:
        print(f"    ⚠️  Archive failed for {pdf_path.name}: {exc}")


def cleanup_old_archives(archive_root: Path) -> None:
    if not archive_root.exists():
        return
    now = datetime.datetime.now()
    for folder in archive_root.iterdir():
        if not folder.is_dir():
            continue
        try:
            folder_date = datetime.datetime.strptime(folder.name, "%Y-%m-%d")
            if (now - folder_date).days > RETENTION_DAYS:
                shutil.rmtree(folder)
                print(f"    🧹 Deleted old archive: {folder.name}")
        except ValueError:
            continue  # Ignore non-date-named subdirectories


# ── Core processing ───────────────────────────────────────────────────────────

def _unique_dest_folder(base_dir: Path, name: str) -> Path:
    """Return a non-existing path, appending _1, _2, … as needed."""
    candidate = base_dir / name
    counter = 1
    while candidate.exists():
        candidate = base_dir / f"{name}_{counter}"
        counter += 1
    return candidate


def _process_single_pdf(
    pdf_file: Path,
    dest_folder: Path,
    dpi: int,
    source_path: Path,
    summary: dict,
) -> None:
    """Process one PDF: detect barcodes, split pages, archive source."""
    doc = fitz.open(str(pdf_file))
    try:
        barcode_pages: dict[str, list] = {}
        current_barcode: str | None = None

        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=dpi)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            found = decode(img)
            print(f"  Page {i + 1}: {len(found)} barcode(s) found")

            for b in found:
                raw = b.data.decode("utf-8", errors="replace")
                print(f"    ➜  Value: '{raw}', Type: {b.type}")
                if raw and b.type in ALLOWED_BARCODE_TYPES:
                    current_barcode = raw
                    break  # First valid barcode on this page wins

            # Accumulate page under the most-recently-seen barcode.
            # Pages that appear before any barcode is encountered are skipped.
            if current_barcode:
                barcode_pages.setdefault(current_barcode, []).append(page)

        for barcode_value, pages in barcode_pages.items():
            filename = f"{sanitize_filename(barcode_value)}.pdf"
            out_path = dest_folder / filename
            save_pdf(pages, out_path)
            print(f"    ✅ Saved: {filename}  ({len(pages)} page(s))")

        summary[pdf_file.name] = len(barcode_pages)
    finally:
        doc.close()  # Always release the file handle (needed before archiving on Windows)

    move_to_archive(pdf_file, source_path)


def extract_barcodes_from_pdf(
    source_dir: str,
    dest_base_dir: str,
    dpi: int = DPI,
) -> str:
    """
    Process all PDFs in source_dir, split by barcode, write to dest_base_dir.
    Returns the path to the output folder created for this run.
    """
    source_path = Path(source_dir)
    date_label  = datetime.datetime.now().strftime("%Y-%m-%d")
    dest_folder = _unique_dest_folder(Path(dest_base_dir), date_label)
    dest_folder.mkdir(parents=True)

    pdf_files = sorted(source_path.glob("*.pdf"))
    if not pdf_files:
        print("⚠️  No PDF files found in the input folder.")
        return str(dest_folder)

    summary: dict[str, int] = {}

    for pdf_file in pdf_files:
        print(f"\n📄 Processing: {pdf_file.name}")
        try:
            _process_single_pdf(pdf_file, dest_folder, dpi, source_path, summary)
        except Exception as exc:
            print(f"    ❌ Error processing {pdf_file.name}: {exc}")
            summary[pdf_file.name] = 0

    cleanup_old_archives(source_path / ARCHIVE_FOLDER_NAME)

    divider = "─" * 60
    print(f"\n{divider}")
    print("📊  Run Summary")
    print(divider)
    print(f"  Input files processed : {len(summary)}")
    for name, count in summary.items():
        print(f"  {name:<40} → {count} PDF(s)")
    print(f"\n✅  Output saved to: {dest_folder}")

    return str(dest_folder)


# ── GUI helpers ───────────────────────────────────────────────────────────────

def _ask_folder(
    config: dict,
    key: str,
    dialog_title: str,
    ask_title: str,
) -> str | None:
    """
    Offer to reuse the last saved folder, or prompt for a new one.
    Returns the chosen path, or None if the user cancelled.
    """
    last = config.get(key, "")
    if last and os.path.exists(last):
        if messagebox.askyesno(ask_title, f"Use last folder?\n\n{last}"):
            return last

    chosen = choose_directory(dialog_title, last)
    if not chosen:
        messagebox.showwarning("Cancelled", f"No folder selected for: {dialog_title.lower()}.")
        return None
    return chosen


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    enable_windows_ansi()

    # ── Root window ────────────────────────────────────────────────────────────
    root = tk.Tk()
    root.title("Barcode Splitter")
    root.geometry("820x560")
    root.configure(bg=BG_COLOR)
    root.resizable(True, True)

    # Header
    tk.Label(
        root,
        text="  ▌ BARCODE SPLITTER ▐  ",
        bg=BG_COLOR,
        fg=FG_COLOR,
        font=(FONT_FACE, 14, "bold"),
        pady=8,
    ).pack(fill="x")

    # Green separator line
    tk.Frame(root, bg=FG_COLOR, height=1).pack(fill="x", padx=8)

    # Scrollable log area
    log_frame = tk.Frame(root, bg=BG_COLOR)
    log_frame.pack(expand=True, fill="both", padx=8, pady=(4, 0))

    scrollbar = tk.Scrollbar(log_frame, troughcolor=BG_COLOR, bg=FG_COLOR)
    scrollbar.pack(side="right", fill="y")

    log_box = tk.Text(
        log_frame,
        wrap="word",
        state="disabled",
        bg=BG_COLOR,
        fg=FG_COLOR,
        insertbackground=FG_COLOR,
        selectbackground=FG_COLOR,
        selectforeground=BG_COLOR,
        font=(FONT_FACE, FONT_SIZE),
        relief="flat",
        yscrollcommand=scrollbar.set,
    )
    log_box.pack(expand=True, fill="both")
    scrollbar.config(command=log_box.yview)

    # Status bar
    tk.Frame(root, bg=FG_COLOR, height=1).pack(fill="x", padx=8, pady=(4, 0))
    status_var = tk.StringVar(value="Initialising…")
    tk.Label(
        root,
        textvariable=status_var,
        bg=BG_COLOR,
        fg=FG_COLOR,
        font=(FONT_FACE, 9),
        anchor="w",
        padx=10,
        pady=4,
    ).pack(fill="x")

    # Redirect stdout → log widget
    sys.stdout = StdoutRedirector(log_box)

    # ── Load config & folder selection ────────────────────────────────────────
    config = load_config()

    input_dir = _ask_folder(config, "last_input", "Select Input Folder", "Input Folder")
    if input_dir is None:
        root.destroy()
        return
    config["last_input"] = input_dir

    output_dir = _ask_folder(config, "last_output", "Select Output Folder", "Output Folder")
    if output_dir is None:
        root.destroy()
        return
    config["last_output"] = output_dir

    save_config(config)
    status_var.set(f"Ready — Input: {input_dir}")

    # ── Completion handlers (always run on the main thread) ───────────────────
    def on_success(result_folder: str) -> None:
        status_var.set(f"Done → {result_folder}")
        messagebox.showinfo("Complete", f"PDFs saved to:\n{result_folder}")
        root.quit()  # Only close after the user dismisses the dialog

    def on_error(msg: str) -> None:
        status_var.set(msg)
        messagebox.showerror("Error", msg)
        root.quit()

    # ── Processing thread ──────────────────────────────────────────────────────
    def processing_thread() -> None:
        try:
            root.after(0, lambda: status_var.set("Processing…"))
            result_folder = extract_barcodes_from_pdf(input_dir, output_dir, DPI)
            print(f"\nProcessing complete!\nOutput: {result_folder}")
            root.after(0, on_success, result_folder)
        except Exception as exc:
            msg = f"Unexpected error: {exc}"
            print(f"\n❌ {msg}")
            root.after(0, on_error, msg)

    threading.Thread(target=processing_thread, daemon=True).start()
    root.mainloop()


if __name__ == "__main__":
    main()
