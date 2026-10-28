@echo off
REM Build barcode_splitter.exe on Windows (Python 3.10.x, 64-bit).
REM Output: dist\barcode_splitter.exe  (single self-contained file)
setlocal
cd /d "%~dp0"

python -m pip install -r requirements.txt || goto :error

python -m PyInstaller --clean --noconfirm --onefile --noconsole ^
  --name barcode_splitter ^
  --version-file version_info.txt ^
  --add-binary "libzbar-64.dll;." ^
  --add-binary "libiconv.dll;." ^
  --add-binary "redist\MSVCR120.dll;." ^
  --add-binary "redist\MSVCP140.dll;." ^
  barcode_splitter.py || goto :error

echo.
echo Build complete: dist\barcode_splitter.exe
exit /b 0

:error
echo Build FAILED.
exit /b 1
