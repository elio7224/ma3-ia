"""create_macro écrit un XML de macro dans gma3_library et l'importe (un seul chemin de création), sans console."""
import os
import xml.etree.ElementTree as ET

import pytest

import tools


@pytest.fixture
def envoyes(monkeypatch):
    liste = []
    monkeypatch.setattr(tools, "ma3", type("Faux", (), {"send": lambda self, c: liste.append(c) or "envoyé"})())
    monkeypatch.setenv("MA3IA_LANGUE", "fr")
    return liste


def _xml_ecrits():
    dossier = tools._dossier_macros()
    return [os.path.join(dossier, f) for f in sorted(os.listdir(dossier)) if f.startswith(tools.PREFIXE_XML_MACRO)]


def _lire(chemin):
    macro = ET.parse(chemin).getroot().find("Macro")
    return macro.get("Name"), [l.get("Command") for l in macro.findall("MacroLine")]


@pytest.mark.parametrize("lignes", [[], ["ClearAll"], ["ClearAll", "Go+ Sequence 1", "Off Sequence 2"]])
def test_xml_et_commande_d_import(envoyes, lignes):
    r = tools.create_macro(7, "Essai", lignes)
    fichiers = _xml_ecrits()
    assert len(fichiers) == 1 and f"({len(lignes)} lignes)" in r
    base = os.path.splitext(os.path.basename(fichiers[0]))[0]
    assert envoyes == [f'Import Macro 7 "{base}" /Overwrite']
    assert _lire(fichiers[0]) == ("Essai", lignes)


def test_guillemets_doubles_et_simples_intacts(envoyes):
    """Cas réel : ligne Lua entourée de " avec des ' à l'intérieur ; le XML les protège (&quot; / &apos;)."""
    ligne = 'Lua "if Confirm(\'Titre\', \'Message\') then Cmd(\'Go+ Macro 1\') end"'
    tools.create_macro(3, 'Nom "double"', [ligne, "ClearAll"])
    fichier = _xml_ecrits()[0]
    assert _lire(fichier) == ('Nom "double"', [ligne, "ClearAll"])
    brut = open(fichier, encoding="utf-8").read()
    assert "&quot;" in brut and "&apos;" in brut


def test_caracteres_speciaux_xml(envoyes):
    tools.create_macro(1, "A&B <x>", ["Echo 'a < b & c'"])
    assert _lire(_xml_ecrits()[0]) == ("A&B <x>", ["Echo 'a < b & c'"])


def test_lignes_none_equivaut_a_zero_ligne(envoyes):
    tools.create_macro(2, "Vide")
    assert _lire(_xml_ecrits()[0]) == ("Vide", [])


def test_overwrite_dans_la_commande(envoyes):
    tools.create_macro(4, "A", ["x"])
    assert envoyes[0].startswith("Import Macro 4 ") and envoyes[0].endswith(" /Overwrite")


def test_anciens_xml_nettoyes_mais_pas_les_recents(envoyes):
    dossier = tools._dossier_macros()
    vieux = os.path.join(dossier, tools.PREFIXE_XML_MACRO + "1_old.xml")
    autre = os.path.join(dossier, "ma_macro_perso.xml")
    for p in (vieux, autre):
        open(p, "w").write("x")
    os.utime(vieux, (0, 0)); os.utime(autre, (0, 0))
    tools.create_macro(5, "A", ["x"])
    assert not os.path.exists(vieux) and os.path.exists(autre)   # seuls nos fichiers ma3ia_tmp_* sont supprimés
    assert len(_xml_ecrits()) == 1


def test_dossier_introuvable_donne_une_erreur(envoyes, monkeypatch):
    monkeypatch.setattr(tools, "DOSSIERS_TEMP_MA3", [])
    r = tools.create_macro(1, "A", ["x"])
    assert r.startswith("Erreur") and envoyes == []


def test_generation_ecrit_un_xml_par_macro_avec_guillemets(envoyes):
    r = tools.generate_macros_from_template(start_macro=1, line_templates=['Lua "Echo(\'{macro}\')"'],
                                            loops=[{"var": "g", "start": 1, "count": 3}], delai_ms=0)
    imports = [c for c in envoyes if c.startswith("Import Macro")]
    assert "Succès" in r and len(imports) == 3 and len(_xml_ecrits()) == 3
    assert [_lire(f)[1] for f in _xml_ecrits()] == [['Lua "Echo(\'1\')"'], ['Lua "Echo(\'2\')"'], ['Lua "Echo(\'3\')"']]
