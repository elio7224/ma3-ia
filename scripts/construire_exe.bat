@echo off
TITLE Construction de MA3-IA
cd /d "%~dp0.."

:: 1) Environnement Python + outils de construction
if not exist "venv" python -m venv venv
venv\Scripts\python.exe -m pip install -q -r requirements-build.txt || goto :erreur

:: 2) Fiche d'identite de l'exe (version, editeur) a partir de ma3ia\version.py
for /f %%V in ('venv\Scripts\python.exe installeur\generer_version.py') do set VERSION=%%V
echo Version %VERSION%

:: 3) Application (mode dossier, sans compression UPX : moins de faux positifs antivirus)
venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --noupx --name MA3-IA ^
  --icon ma3ia\assets\ma3ia.ico --version-file build\version_info.txt --paths ma3ia ^
  --add-data "ma3ia\assets\ma3ia.ico;assets" --add-data "ma3ia\web\index.html;web" ^
  --add-data "ma3ia\memo_grandma3.md;." --add-data "plugin\ai_index.lua;plugin" ^
  --collect-submodules keyring.backends ^
  ma3ia\desktop.py || goto :erreur

:: 4) Installateur (si Inno Setup 6 est installe : winget install JRSoftware.InnoSetup)
set ISCC=
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
if "%ISCC%"=="" (
    echo Inno Setup absent : seul dist\MA3-IA\MA3-IA.exe a ete construit.
    goto :fin
)
"%ISCC%" /Q /DVersion=%VERSION% installeur\MA3-IA.iss || goto :erreur
echo.
echo Installateur : dist\MA3-IA-Setup-%VERSION%.exe
goto :fin

:erreur
echo.
echo ECHEC de la construction.
if /i not "%~1"=="silencieux" pause
exit /b 1
:fin
if /i not "%~1"=="silencieux" pause
