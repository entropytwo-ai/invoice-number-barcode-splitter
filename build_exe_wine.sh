#!/usr/bin/env bash
# Cross-build barcode_splitter.exe from Linux using Wine + Windows Python 3.10.
# Prerequisites: wine64 installed, and Windows Python 3.10 (64-bit) with the
# packages from requirements.txt installed inside $WINEPREFIX at $WINPY.
#   (Tip: the python.org per-component MSIs can be unpacked with `msiextract`
#    into $WINEPREFIX/drive_c/Python310, then run `python.exe -m ensurepip`.)
set -euo pipefail
cd "$(dirname "$0")"

export WINEPREFIX="${WINEPREFIX:-$HOME/.wine64}"
export WINEDEBUG="${WINEDEBUG:--all}"
WINE="${WINE:-$(command -v wine64 || echo /usr/lib/wine/wine64)}"
WINPY="${WINPY:-C:\\Python310\\python.exe}"

# </dev/null avoids "init_sys_streams: Invalid handle" under Wine.
"$WINE" "$WINPY" -m PyInstaller --clean --noconfirm --onefile --noconsole \
  --name barcode_splitter \
  --version-file version_info.txt \
  --add-binary "libzbar-64.dll;." \
  --add-binary "libiconv.dll;." \
  --add-binary "redist/MSVCR120.dll;." \
  --add-binary "redist/MSVCP140.dll;." \
  barcode_splitter.py </dev/null 2>&1 | cat

echo "Build complete: dist/barcode_splitter.exe"
