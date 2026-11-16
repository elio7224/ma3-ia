"""Windows et macOS : chemins par défaut, dossier de config, nom du coffre, langue du système, icône macOS."""
import os
import struct
import subprocess

import i18n
import reglages
import tools

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_bibliotheque_par_defaut_selon_plateforme():
    assert reglages.bibliotheque_defaut("win32") == r"C:\ProgramData\MALightingTechnology\gma3_library"
    assert reglages.bibliotheque_defaut("darwin") == os.path.join(os.path.expanduser("~"), "MALightingTechnology", "gma3_library")


def test_dossiers_temp_par_defaut_dans_la_bibliotheque_de_la_plateforme():
    # conftest remplace tools.DOSSIERS_TEMP_MA3 : on vérifie la valeur calculée à l'import, dans le même ordre.
    attendus = reglages.dossiers_temp(reglages.BIBLIOTHEQUE_DEFAUT)
    assert attendus[0].endswith(os.path.join("datapools", "groups", "Temp"))
    assert attendus[-1].endswith(os.path.join("appearances", "Temp"))
    assert reglages.DEFAUTS["dossier_bibliotheque"] == reglages.BIBLIOTHEQUE_DEFAUT
    assert tools.BIBLIOTHEQUE_DEFAUT == reglages.BIBLIOTHEQUE_DEFAUT


def test_dossier_config_selon_plateforme(monkeypatch):
    monkeypatch.delenv("MA3IA_CONFIG_DIR", raising=False)
    maison = os.path.expanduser("~")
    monkeypatch.setattr(reglages, "WINDOWS", False)
    monkeypatch.setattr(reglages, "MAC", True)
    assert reglages.dossier_config() == os.path.join(maison, "Library", "Application Support", "ma3-ia")
    monkeypatch.setattr(reglages, "MAC", False)
    monkeypatch.setattr(reglages, "WINDOWS", True)
    monkeypatch.setenv("APPDATA", os.path.join(maison, "AppData"))
    assert reglages.dossier_config() == os.path.join(maison, "AppData", "ma3-ia")
    monkeypatch.setenv("MA3IA_CONFIG_DIR", "/tmp/cfg")
    assert reglages.dossier_config() == "/tmp/cfg"


def test_nom_du_coffre(monkeypatch):
    monkeypatch.setattr(reglages, "WINDOWS", False)
    monkeypatch.setattr(reglages, "MAC", True)
    assert reglages.nom_coffre() == "trousseau macOS"
    monkeypatch.setattr(reglages, "MAC", False)
    monkeypatch.setattr(reglages, "WINDOWS", True)
    assert reglages.nom_coffre() == "coffre Windows"


def test_bibliotheque_avec_tilde_developpee():
    val, err = reglages._valider("dossier_bibliotheque", " '~/MALightingTechnology/gma3_library' ")
    assert err is None
    assert val == os.path.join(os.path.expanduser("~"), "MALightingTechnology", "gma3_library")


def test_langue_mac(monkeypatch):
    sortie = '(\n    "en-FR",\n    "fr-FR"\n)\n'
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout=sortie))
    assert i18n._langue_mac() == "en-FR"
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(OSError("pas de defaults")))
    assert i18n._langue_mac() is None


def test_icone_macos_valide():
    with open(os.path.join(RACINE, "ma3ia", "assets", "ma3ia.icns"), "rb") as f:
        data = f.read()
    assert data[:4] == b"icns" and struct.unpack(">I", data[4:8])[0] == len(data)
    types, pos = set(), 8
    while pos < len(data):
        t, n = data[pos:pos + 4], struct.unpack(">I", data[pos + 4:pos + 8])[0]
        assert data[pos + 8:pos + 16] == b"\x89PNG\r\n\x1a\n"
        types.add(t)
        pos += n
    assert pos == len(data)
    assert {b"icp4", b"ic07", b"ic10"} <= types
