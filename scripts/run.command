#!/bin/bash
# MA3-IA sous macOS, depuis le code source : double-clic dans le Finder (ou ./scripts/run.command).
# La première fois (ou si requirements.txt a changé) : crée le venv et installe les dépendances.
# Ensuite : ouvre directement l'application.
cd "$(dirname "$0")/.." || exit 1

# Python 3.10 ou plus (anthropic l'exige). Le python3 fourni avec macOS est souvent trop ancien (3.9).
trouver_python() {
    for p in python3.13 python3.12 python3.11 python3.10 python3 \
             /Library/Frameworks/Python.framework/Versions/3.1[0-9]/bin/python3 \
             /opt/homebrew/bin/python3 /usr/local/bin/python3; do
        if command -v "$p" >/dev/null 2>&1 && "$p" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
            command -v "$p"
            return 0
        fi
    done
    return 1
}

installer=0
[ -x venv/bin/python ] || installer=1
[ -f venv/.installe ] || installer=1
[ -f venv/.installe ] && [ requirements.txt -nt venv/.installe ] && installer=1

if [ "$installer" = 1 ]; then
    echo "Installation de MA3-IA, patiente un instant..."
    if [ ! -x venv/bin/python ]; then
        PY=$(trouver_python) || {
            echo
            echo "Python 3.10 ou plus est introuvable (le python3 de macOS est trop ancien)."
            echo "Installe Python 3.12 depuis https://www.python.org/downloads/macos/ puis relance ce script."
            read -r -p "Appuie sur Entrée pour fermer."
            exit 1
        }
        "$PY" -m venv venv || exit 1
    fi
    venv/bin/python -m pip install -q --upgrade pip
    venv/bin/python -m pip install -q -r requirements.txt || {
        echo; echo "Échec de l'installation."; read -r -p "Appuie sur Entrée pour fermer."; exit 1; }
    echo ok > venv/.installe
fi

# Lance l'application en arrière-plan, détachée du Terminal.
nohup venv/bin/python ma3ia/desktop.py >/dev/null 2>&1 &
