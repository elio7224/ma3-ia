@echo off
TITLE MA3-IA - installation
cd /d "%~dp0"

:: Installation uniquement la premiere fois (ou si requirements.txt a change) :
:: les lancements suivants ouvrent directement l'app et cette fenetre noire se ferme aussitot.
set INSTALLER=0
if not exist "venv\Scripts\pythonw.exe" set INSTALLER=1
if not exist "venv\.installe" set INSTALLER=1
if exist "venv\.installe" for /f %%R in ('powershell -NoProfile -Command "[int]((Get-Item requirements.txt).LastWriteTime -gt (Get-Item venv\.installe).LastWriteTime)"') do if "%%R"=="1" set INSTALLER=1

if "%INSTALLER%"=="1" (
    echo Installation de MA3-IA, patiente un instant...
    if not exist "venv" python -m venv venv
    venv\Scripts\python.exe -m pip install -q --upgrade pip
    venv\Scripts\python.exe -m pip install -q -r requirements.txt || (echo. & echo Echec de l'installation. & pause & exit /b 1)
    echo ok> "venv\.installe"
    :: Raccourci "MA3-IA" sur le Bureau : lance l'app sans aucune fenetre noire.
    call "%~dp0creer_raccourci.bat" silencieux
)

:: Lance l'application sans console (pythonw), puis cette fenetre se ferme.
start "" "venv\Scripts\pythonw.exe" desktop.py
exit
