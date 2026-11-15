@echo off
TITLE Construction de MA3-IA.exe
cd /d "%~dp0"

if not exist "venv" python -m venv venv
call venv\Scripts\activate
pip install -q -r requirements-build.txt

pyinstaller --noconfirm --clean --windowed --name MA3-IA ^
  --icon ma3ia.ico --add-data "ma3ia.ico;." ^
  --add-data "index.html;." --add-data "ai_index.lua;." --add-data "memo_grandma3.md;." ^
  --collect-submodules keyring.backends ^
  desktop.py

echo.
echo Termine : dist\MA3-IA\MA3-IA.exe  (copie tout le dossier dist\MA3-IA pour le deplacer)
pause
