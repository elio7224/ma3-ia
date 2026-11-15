"""Installation automatique du plugin AI_Index, sans console."""
import base64
import re

import pytest

import plugin_ma3
import reglages
import tools


def test_xml_au_format_export_grandma3():
    lua = ("-- é\n" * 600).encode("utf-8")                  # > 1024 octets : plusieurs blocs
    xml = plugin_ma3.generer_xml(lua, "1.2.0.0")
    blocs = re.findall(r'Base64="([^"]*)"', xml)
    assert f'<FileContent Size="{len(blocs)}">' in xml and len(blocs) == -(-len(lua) // 1024)
    assert all(len(base64.b64decode(b)) == 1024 for b in blocs[:-1])
    assert b"".join(base64.b64decode(b) for b in blocs) == lua
    assert '<UserPlugin Name="AI_Index" Version="1.2.0.0">' in xml and "<ComponentLua>" in xml


@pytest.fixture
def console(tmp_path, monkeypatch):
    monkeypatch.setenv("MA3IA_CONFIG_DIR", str(tmp_path / "cfg"))
    reglages.enregistrer({"dossier_bibliotheque": str(tmp_path / "lib")})
    envoyes = []
    monkeypatch.setattr(tools, "ma3", type("F", (), {"send": lambda self, c: envoyes.append(c) or "envoyé"})())
    monkeypatch.setattr(plugin_ma3, "PAUSE_APRES_IMPORT_S", 0)
    return envoyes, tmp_path / "lib" / "datapools" / "plugins" / "ai_index.xml"


def test_deja_installe_pas_de_doublon(console, monkeypatch):
    envoyes, xml = console
    monkeypatch.setattr(tools, "_lancer_plugin_index", lambda: None)          # le plugin répond
    r = plugin_ma3.installer()
    assert r["ok"] and r["deja_installe"] and not xml.exists()
    assert not any(c.startswith("Import") for c in envoyes)


def test_installation_puis_verification(console, monkeypatch):
    envoyes, xml = console
    reponses = iter(["pas d'index", None])                                     # absent, puis présent après import
    monkeypatch.setattr(tools, "_lancer_plugin_index", lambda: next(reponses))
    r = plugin_ma3.installer()
    assert r["ok"] and not r["deja_installe"] and xml.exists()
    assert envoyes == ['Import Plugin Library "ai_index.xml"']
    with open(reglages.chemin_plugin_lua(), "rb") as f:
        lua = f.read()
    contenu = xml.read_text(encoding="utf-8-sig")
    assert b"".join(base64.b64decode(b) for b in re.findall(r'Base64="([^"]*)"', contenu)) == lua


def test_echec_signale(console, monkeypatch):
    monkeypatch.setattr(tools, "_lancer_plugin_index", lambda: "pas d'index")
    r = plugin_ma3.installer()
    assert not r["ok"] and "confirm" in r["message"]
