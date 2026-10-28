@echo off
REM Build Barcode Splitter on Windows (Python 3.10.x, 64-bit).
REM Output: dist\barcode_splitter\barcode_splitter.exe  (+ _internal\ folder)
REM
REM Antivirus false positives: the stock prebuilt PyInstaller bootloader is
REM flagged by some ML scanners (e.g. Defender "Wacatac.B!ml"). Two mitigations:
REM   * --onedir instead of --onefile (no self-extracting payload)
REM   * Optional: rebuild PyInstaller's bootloader from source first. This needs
REM     a C compiler (Visual Studio Build Tools, "Desktop development with C++"):
REM         set PYINSTALLER_COMPILE_BOOTLOADER=1
REM         pip install --force-reinstall --no-binary pyinstaller pyinstaller
setlocal
cd /d "%~dp0"

python -m pip install -r requirements.txt || goto :error

python -m PyInstaller --clean --noconfirm --onedir --noconsole ^
  --name barcode_splitter ^
  --version-file version_info.txt ^
  --add-binary "libzbar-64.dll;." ^
  --add-binary "libiconv.dll;." ^
  --add-binary "redist\MSVCR120.dll;." ^
  --add-binary "redist\MSVCP140.dll;." ^
  barcode_splitter.py || goto :error

echo.
echo Build complete: dist\barcode_splitter\barcode_splitter.exe
echo Ship the whole dist\barcode_splitter folder (zip it).
exit /b 0

:error
echo Build FAILED.
exit /b 1
