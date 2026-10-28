#!/usr/bin/env bash
# Cross-build the Windows release from Linux using Wine + Windows Python 3.10.
#
# Output: dist/barcode_splitter/            (folder: barcode_splitter.exe + _internal/)
#         dist/barcode_splitter-v<ver>-windows-x64.zip
#
# Antivirus false positives: PyInstaller's stock prebuilt bootloader is shared
# by countless programs (including real malware), so ML-based scanners such as
# Microsoft Defender ("Wacatac.B!ml") often flag anything that contains it,
# especially single-file (--onefile) builds. This script therefore:
#   1. compiles PyInstaller's bootloader from source with mingw-w64, and
#   2. builds in --onedir mode (no self-extracting payload).
#
# Set BOOTLOADER_DIR=/path/to/dir-with-runw.exe to reuse a compiled bootloader.
#
# Prerequisites:
#   sudo apt install wine64 mingw-w64 zip
#   Windows Python 3.10 (64-bit) inside $WINEPREFIX at $WINPY with
#   `pip install -r requirements.txt` done. (Tip: the python.org per-component
#   MSIs can be unpacked with `msiextract` into $WINEPREFIX/drive_c/Python310,
#   then run `python.exe -m ensurepip`.)
set -euo pipefail
cd "$(dirname "$0")"

export WINEPREFIX="${WINEPREFIX:-$HOME/.wine64}"
export WINEDEBUG="${WINEDEBUG:--all}"
WINE="${WINE:-$(command -v wine64 || echo /usr/lib/wine/wine64)}"
WINPY="${WINPY:-C:\\Python310\\python.exe}"
VERSION="$(grep -oP "FileVersion', '\K[0-9.]+" version_info.txt)"

# ── 1. Build PyInstaller's bootloader from source ────────────────────────────
# Wine's Python needs every std stream to be a pipe or /dev/null (a plain
# redirected file gives "init_sys_streams: Invalid handle"), hence `2>&1 | cat`.
winpy() { "$WINE" "$WINPY" "$@" </dev/null 2>&1 | cat; }
PYI_VER="$(winpy -c "import PyInstaller;print(PyInstaller.__version__)" | tr -d '\r')"
PYI_DIR="$(winpy -c "import PyInstaller,os;print(os.path.dirname(PyInstaller.__file__))" | tr -d '\r')"
BOOT_DST="$("$WINE" winepath -u "$PYI_DIR\\bootloader\\Windows-64bit-intel" </dev/null 2>/dev/null | cat)"
[ -d "$BOOT_DST" ] || { echo "Bootloader dir not found: $BOOT_DST"; exit 1; }
[ -d "$BOOT_DST.orig" ] || cp -r "$BOOT_DST" "$BOOT_DST.orig"
if [ -n "${BOOTLOADER_DIR:-}" ]; then
  # Reuse a previously compiled bootloader (e.g. one already verified clean on
  # VirusTotal) - ML scanners can score each fresh compile differently.
  echo "Using prebuilt bootloader from $BOOTLOADER_DIR"
  cp "$BOOTLOADER_DIR"/*.exe "$BOOT_DST/"
else
  WORK="$(mktemp -d)"
  trap 'rm -rf "$WORK"' EXIT
  echo "Compiling PyInstaller $PYI_VER bootloader with mingw-w64..."
  pip download -q --no-binary :all: --no-deps "pyinstaller==$PYI_VER" -d "$WORK"
  tar xzf "$WORK"/pyinstaller-*.tar.gz -C "$WORK"
  (
    cd "$WORK"/pyinstaller-*/bootloader
    CC=x86_64-w64-mingw32-gcc AR=x86_64-w64-mingw32-ar WINDRES=x86_64-w64-mingw32-windres \
      python3 ./waf distclean configure --target-arch=64bit all >/dev/null
  )
  cp "$WORK"/pyinstaller-*/PyInstaller/bootloader/Windows-64bit-intel/*.exe "$BOOT_DST/"
fi

# ── 2. Build (onedir). </dev/null avoids "init_sys_streams: Invalid handle". ──
rm -rf build dist
winpy -m PyInstaller --clean --noconfirm --onedir --noconsole \
  --name barcode_splitter \
  --version-file version_info.txt \
  --add-binary "libzbar-64.dll;." \
  --add-binary "libiconv.dll;." \
  --add-binary "redist/MSVCR120.dll;." \
  --add-binary "redist/MSVCP140.dll;." \
  barcode_splitter.py

# ── 3. Package ────────────────────────────────────────────────────────────────
ZIP="barcode_splitter-v${VERSION}-windows-x64.zip"
(cd dist && zip -qr "$ZIP" barcode_splitter)
echo "Build complete: dist/barcode_splitter/barcode_splitter.exe"
echo "Release archive: dist/$ZIP"
