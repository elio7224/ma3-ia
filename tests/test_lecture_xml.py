"""Tests de la compaction et du découpage des exports XML (sans console grandMA3)."""
import tools

XML_SEQUENCE = """﻿<?xml version="1.0" encoding="UTF-8"?>
<GMA3 DataVersion="2.5.1.0">
  <Sequence Name="Test" Guid="AA BB" Tracking="Yes">
    <Cue Name="Entrée" No="  2">
      <Part Name="Entrée" Guid="CC" Mode="0" Action="Pool Default">
        <DependencyExport Size="1">
          <Dependency Address="ShowData.DataPools.Default.PresetPools.Dimmer.70"><Preset Guid="X"/></Dependency>
        </DependencyExport>
        <PresetData Size="3">
          <Phaser IDType="0" ID="401" Attribute="Dimmer" Fade="1.50" GridPos="0"><Step Function="Dimmer" Absolute="*70"/></Phaser>
          <Phaser IDType="0" ID="402" Attribute="Dimmer" Fade="1.50" GridPos="1"><Step Function="Dimmer" Absolute="*70"/></Phaser>
          <Phaser IDType="0" ID="403" Attribute="Dimmer" Fade="1.50" GridPos="2"><Step Function="Dimmer" Absolute="*70"/></Phaser>
          <Phaser IDType="0" ID="410" Attribute="Dimmer" Fade="1.50" GridPos="3"><Step Function="Dimmer" Absolute="*20"/></Phaser>
        </PresetData>
      </Part>
    </Cue>
  </Sequence>
</GMA3>
"""


def _ecrire(tmp_path, texte):
    f = tmp_path / "objet.xml"
    f.write_text(texte, encoding="utf-8")
    return str(f)


def test_compacter_regroupe_et_retire_le_bruit(tmp_path):
    t = tools.compacter_xml(_ecrire(tmp_path, XML_SEQUENCE))
    assert "Guid" not in t and "Pool Default" not in t and "<" not in t
    assert "Cue Name=Entrée No=2" in t
    assert "[ID 401-403] Phaser Attribute=Dimmer Fade=1.50 -> Step Function=Dimmer Absolute=*70" in t
    assert "[ID 410]" in t and "Absolute=*20" in t
    assert "Dépendances" in t and "PresetPools.Dimmer.70" in t


def test_plages_ids():
    assert tools._plages(["401", "402", "403", "410"]) == "401-403, 410"
    assert tools._plages(["301.1.1", "301.1.2", "301.2.1"]) == "301.1.1-2, 301.2.1"


def test_citer_sans_echappement():
    assert tools._citer("ClearAll") == "ClearAll"
    assert tools._citer("Store Group 1") == '"Store Group 1"'
    assert tools._citer('Lua "Cmd(\'Go\')"') == '«Lua "Cmd(\'Go\')"»'


def test_decouper_sans_couper_les_lignes():
    texte = "\n".join(f"ligne {i:04d}" for i in range(3000))
    parties = tools._decouper(texte, 1000)
    assert len(parties) > 1 and all(len(p) <= 1000 for p in parties)
    assert "\n".join(parties) == texte


def test_xml_illisible_renvoye_brut(tmp_path):
    assert tools.compacter_xml(_ecrire(tmp_path, "pas du xml <")) == "pas du xml <"


def test_lire_xml_temp_par_parties(tmp_path, monkeypatch):
    chemin = _ecrire(tmp_path, XML_SEQUENCE)
    monkeypatch.setattr(tools, "INDEX_OBJETS", {"sequences": {"100": "Test"}})
    monkeypatch.setattr(tools, "_exporter_objet", lambda s, n: chemin)
    monkeypatch.setattr(tools, "TAILLE_PARTIE", 120)
    r1 = tools.lire_xml_temp("sequences/100")
    assert "partie 1/" in r1 and "partie=2" in r1
    r2 = tools.lire_xml_temp("sequences/100", partie=2)
    assert "partie 2/" in r2
    assert "inexistante" in tools.lire_xml_temp("sequences/100", partie=99)

