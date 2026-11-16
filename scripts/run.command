#!/bin/bash
# MA3-IA sous macOS, depuis le code source : double-clic dans le Finder (ou ./scripts/run.command).
# Rien à installer avant : s'il n'y a pas de Python 3.10+ sur le Mac, le script télécharge l'outil `uv`
# et un Python 3.12 privé dans le dossier .outils/ du projet (sans droits administrateur, sans toucher au système).
# La première fois (ou si requirements.txt a changé) : crée le venv et installe les dépendances.
# Ensuite : ouvre directement l'application.
cd "$(dirname "$0")/.." || exit 1

OUTILS="$PWD/.outils"
UV="$OUTILS/uv"
export UV_PYTHON_INSTALL_DIR="$OUTILS/python"   # Python privé de l'app, supprimé avec le projet
export UV_CACHE_DIR="$OUTILS/cache"

echec() {
    echo
    echo "❌ $1"
    read -r -p "Appuie sur Entrée pour fermer."
    exit 1
}

# Python 3.10 ou plus déjà présent (python.org, Homebrew…). Le python3 fourni avec macOS est trop ancien (3.9).
trouver_python() {
    for p in python3.13 python3.12 python3.11 python3.10 python3 \
             /opt/homebrew/bin/python3.1[0-9] /usr/local/bin/python3.1[0-9] \
             /Library/Frameworks/Python.framework/Versions/3.1[0-9]/bin/python3; do
        if command -v "$p" >/dev/null 2>&1 && "$p" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
            command -v "$p"
            return 0
        fi
    done
    return 1
}

# Télécharge uv (binaire officiel publié sur GitHub par Astral) dans .outils/.
installer_uv() {
    [ -x "$UV" ] && return 0
    case "$(uname -m)" in
        arm64) arch=aarch64 ;;
        x86_64) arch=x86_64 ;;
        *) return 1 ;;
    esac
    echo "Téléchargement de l'outil d'installation Python (uv)..."
    mkdir -p "$OUTILS"
    curl -fsSL "https://github.com/astral-sh/uv/releases/latest/download/uv-$arch-apple-darwin.tar.gz" \
        | tar -xz -C "$OUTILS" --strip-components 1 || return 1
    [ -x "$UV" ]
}

installer=0
[ -x venv/bin/python ] || installer=1
[ -f venv/.installe ] || installer=1
[ -f venv/.installe ] && [ requirements.txt -nt venv/.installe ] && installer=1

if [ "$installer" = 1 ]; then
    echo "Installation de MA3-IA, patiente un instant (la première fois : 1 à 3 minutes)..."
    if [ -x venv/bin/python ] && ! venv/bin/python -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
        rm -rf venv                                # ancien venv en Python 3.9 : on le refait
    fi
    if [ ! -x venv/bin/python ]; then
        if PY=$(trouver_python); then
            "$PY" -m venv venv || echec "Création de l'environnement Python impossible."
        else
            installer_uv || echec "Téléchargement de uv impossible : vérifie ta connexion Internet."
            echo "Installation d'un Python 3.12 privé pour MA3-IA..."
            "$UV" venv -q --seed --python 3.12 venv || echec "Installation de Python 3.12 impossible."
        fi
    fi
    venv/bin/python -m pip install -q --upgrade pip
    venv/bin/python -m pip install -q -r requirements.txt || echec "Échec de l'installation des dépendances."
    echo ok > venv/.installe
    echo "✅ Installation terminée."
fi

# Lance l'application en arrière-plan, détachée du Terminal.
nohup venv/bin/python ma3ia/desktop.py >/dev/null 2>&1 &
