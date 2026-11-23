"""modifier_xml : remplacements sur le XML exporté, sauvegarde, import (sans console grandMA3)."""
import os

import tools

XML = '<?xml version="1.0"?>\n<GMA3><Layout Name="Scene"><Item Name="A"/><Item Name="A"/></Layout></GMA3>\n'


class FauxMA3:
    def __init__(self):
        self.envoyes = []

    def send(self, cmd):
        self.envoyes.append(cmd)


def _preparer(monkeypatch):
    faux = FauxMA3()
    monkeypatch.setattr(tools, "ma3", faux)
    monkeypatch.setattr(tools, "sauvegarder_avant_masse", lambda: "")

    def export(section, numero):
        chemin = os.path.join(tools._dossier_section(section), f"{numero}.xml")
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(XML)
        return chemin
    monkeypatch.setattr(tools, "_exporter_objet", export)
    return faux


def test_remplacement_importe_et_sauvegarde(monkeypatch):
    faux = _preparer(monkeypatch)
    r = tools.modifier_xml("layouts", "3", [{"ancien": 'Name="Scene"', "nouveau": 'Name="Neuf"'}])
    assert "modifié" in r and faux.envoyes[0].startswith('Import Layout 3 "ma3ia_tmp_layouts_3_') and faux.envoyes[0].endswith("/Overwrite")
    dossier = os.path.dirname(tools._dossier_section("layouts"))
    fichiers = os.listdir(dossier)
    assert any(f.startswith("ma3ia_sauvegarde_3_") for f in fichiers)
    base = faux.envoyes[0].split('"')[1]
    assert 'Name="Neuf"' in open(os.path.join(dossier, base + ".xml"), encoding="utf-8").read()


def test_garde_fous(monkeypatch):
    faux = _preparer(monkeypatch)
    assert "introuvable" in tools.modifier_xml("layouts", "3", [{"ancien": "zzz", "nouveau": "y"}])
    assert "2 fois" in tools.modifier_xml("layouts", "3", [{"ancien": 'Name="A"', "nouveau": 'Name="B"'}])
    assert "invalide" in tools.modifier_xml("layouts", "3", [{"ancien": "<Layout", "nouveau": "<Layout<"}])
    assert "non modifiable" in tools.modifier_xml("appearances", "3", [{"ancien": "a", "nouveau": "b"}])
    assert "Aperçu" in tools.modifier_xml("layouts", "3", [{"ancien": 'Name="A"', "nouveau": "Name=\"B\"", "tout": True}], dry_run=True)
    assert faux.envoyes == []


def test_chercher_garde_tous_les_attributs():
    xml = '<G>\n  <Item Name="A" Border="3" Color="red"/>\n  <Item Name="B" Border="1"/>\n</G>'
    r = tools._lignes_contenant(xml, 'name="a"')
    assert r == '<Item Name="A" Border="3" Color="red"/>'
    assert "<G>" in tools._lignes_contenant(xml, 'name="b"', contexte=2)
    assert "Aucune ligne" in tools._lignes_contenant(xml, "zzz")
