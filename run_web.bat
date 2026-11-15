@echo off
TITLE Serveur web MA3-IA
color 0A
echo ========================================================
echo   LANCEMENT DE L'AGENT GRANDMA3
echo ========================================================

:: Se placer dans le dossier du projet
cd /d "%~dp0"

:: Vérifier si le venv existe, sinon le créer
if not exist "venv" (
    echo [INFO] Création de l'environnement virtuel venv...
    python -m venv venv
)

:: Activer le venv
echo [INFO] Activation de l'environnement virtuel...
call venv\Scripts\activate

:: Installer ou mettre à jour les dépendances si besoin
python -m pip install --upgrade pip >nul 2>&1
if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    pip install fastapi uvicorn pydantic requests anthropic python-osc
)

:: Lancer app.py (le vrai nom de ton fichier)
echo ========================================================
echo   TOUT EST PRÊT ! LANCEMENT DU SERVEUR...
echo ========================================================
python app.py

pause