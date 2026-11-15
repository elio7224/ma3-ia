"""Écrit build/version_info.txt : la fiche « Propriétés > Détails » de MA3-IA.exe (éditeur, version, description).

Un exe sans ces informations paraît plus suspect aux antivirus et à Windows. Usage : python installeur/generer_version.py
"""
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
from version import DESCRIPTION, EDITEUR, NOM, URL, VERSION  # noqa: E402

nums = tuple(int(x) for x in (VERSION.split(".") + ["0", "0", "0"])[:4])
contenu = f"""# Généré par installeur/generer_version.py — ne pas modifier à la main.
VSVersionInfo(
  ffi=FixedFileInfo(filevers={nums}, prodvers={nums}, mask=0x3f, flags=0x0, OS=0x40004,
                    fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040c04b0', [
      StringStruct('CompanyName', '{EDITEUR}'),
      StringStruct('FileDescription', '{DESCRIPTION}'),
      StringStruct('FileVersion', '{VERSION}'),
      StringStruct('InternalName', '{NOM}'),
      StringStruct('LegalCopyright', 'Copyright (c) 2026 {EDITEUR} - MIT License'),
      StringStruct('OriginalFilename', '{NOM}.exe'),
      StringStruct('ProductName', '{NOM} - {DESCRIPTION}'),
      StringStruct('ProductVersion', '{VERSION}'),
      StringStruct('Comments', '{URL} - independent project, not affiliated with MA Lighting')])]),
    VarFileInfo([VarStruct('Translation', [1036, 1200])])
  ]
)
"""
os.makedirs(os.path.join(RACINE, "build"), exist_ok=True)
with open(os.path.join(RACINE, "build", "version_info.txt"), "w", encoding="utf-8") as f:
    f.write(contenu)
print(VERSION)
