#!/bin/bash
# Construit MA3-IA.app et l'image disque MA3-IA-<version>.dmg sous macOS (équivalent de construire_exe.bat).
# Usage : ./scripts/construire_app.sh       Résultat : dist/MA3-IA.app et dist/MA3-IA-<version>.dmg
set -euo pipefail
cd "$(dirname "$0")/.."

# 1) Environnement Python + outils de construction (Python 3.10 ou plus)
if [ ! -x venv/bin/python ]; then
    PY=""
    for p in python3.13 python3.12 python3.11 python3.10 python3; do
        if command -v "$p" >/dev/null 2>&1 && "$p" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
            PY=$p; break
        fi
    done
    [ -n "$PY" ] || { echo "Python 3.10 ou plus introuvable (https://www.python.org/downloads/macos/)."; exit 1; }
    "$PY" -m venv venv
fi
venv/bin/python -m pip install -q -r requirements-build.txt

VERSION=$(cd ma3ia && ../venv/bin/python -c "from version import VERSION; print(VERSION)")
echo "Version $VERSION"

# 2) Application (.app). Séparateur de --add-data : « : » sous macOS (« ; » sous Windows).
venv/bin/python -m PyInstaller --noconfirm --clean --windowed --name MA3-IA \
  --icon ma3ia/assets/ma3ia.icns --osx-bundle-identifier io.github.elio7224.ma3ia --paths ma3ia \
  --add-data "ma3ia/assets/ma3ia.ico:assets" --add-data "ma3ia/web/index.html:web" \
  --add-data "ma3ia/memo_grandma3.md:." --add-data "plugin/ai_index.lua:plugin" \
  --collect-submodules keyring.backends \
  ma3ia/desktop.py

# 3) Info.plist : version, et texte de la demande d'accès au réseau local (OSC vers une console du réseau).
PLIST=dist/MA3-IA.app/Contents/Info.plist
plutil -replace CFBundleShortVersionString -string "$VERSION" "$PLIST"
plutil -replace CFBundleVersion -string "$VERSION" "$PLIST"
plutil -replace NSHumanReadableCopyright -string "MIT License - elio7224" "$PLIST"
plutil -replace NSLocalNetworkUsageDescription -string \
  "MA3-IA envoie des commandes OSC à ta console grandMA3 sur le réseau local. / MA3-IA sends OSC commands to your grandMA3 console on the local network." "$PLIST"
# Info.plist modifié : signature ad hoc à refaire (sinon macOS considère l'app comme endommagée).
codesign --force --deep --sign - dist/MA3-IA.app

# 4) Image disque avec un raccourci vers /Applications (glisser-déposer).
DMG_DIR=build/dmg
rm -rf "$DMG_DIR" && mkdir -p "$DMG_DIR"
cp -R dist/MA3-IA.app "$DMG_DIR/"
ln -s /Applications "$DMG_DIR/Applications"
rm -f "dist/MA3-IA-$VERSION.dmg"
hdiutil create -quiet -volname "MA3-IA $VERSION" -srcfolder "$DMG_DIR" -ov -format UDZO "dist/MA3-IA-$VERSION.dmg"
echo
echo "Application : dist/MA3-IA.app"
echo "Image disque : dist/MA3-IA-$VERSION.dmg"
