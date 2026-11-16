"""create_macro passe par _commandes_macro (un seul chemin de création), sans console."""
import pytest

import tools


@pytest.fixture
def envoyes(monkeypatch):
    liste = []
    monkeypatch.setattr(tools, "ma3", type("Faux", (), {"send": lambda self, c: liste.append(c) or "envoyé"})())
    monkeypatch.setenv("MA3IA_LANGUE", "fr")
    return liste


def _attendu(n, nom, lignes):
    cmds = [f"Delete Macro {n} /noconfirm", f"Store Macro {n}", f"ChangeDestination Macro {n}"]
    for i, l in enumerate(lignes, 1):
        cmds.append("Insert")
        cmds.append(f'Set {i} Property "Command" "{l}"')
    return cmds + ["ChangeDestination Root", f'Label Macro {n} "{nom}"']


@pytest.mark.parametrize("lignes", [[], ["ClearAll"], ["ClearAll", "Go+ Sequence 1", "Off Sequence 2"]])
def test_sequence_de_commandes(envoyes, lignes):
    r = tools.create_macro(7, "Essai", lignes)
    assert envoyes == _attendu(7, "Essai", lignes) == tools._commandes_macro(7, "Essai", lignes)
    assert f"({len(lignes)} lignes)" in r


def test_insert_avant_chaque_ligne_y_compris_la_premiere(envoyes):
    tools.create_macro(1, "A", ["x", "y", "z"])
    assert envoyes.count("Insert") == 3
    assert envoyes[3] == "Insert" and envoyes[4].startswith("Set 1 ")


def test_delete_avant_store(envoyes):
    tools.create_macro(4, "A", ["x"])
    assert envoyes.index("Delete Macro 4 /noconfirm") < envoyes.index("Store Macro 4")


def test_lignes_none_equivaut_a_zero_ligne(envoyes):
    tools.create_macro(2, "Vide")
    assert envoyes == _attendu(2, "Vide", [])


@pytest.mark.parametrize("args", [(3, "Ok", ['Set "x"']), (3, 'Nom "double"', ["ok"])])
def test_guillemets_doubles_refuses(envoyes, args):
    r = tools.create_macro(*args)
    assert r.startswith("Erreur : guillemets doubles interdits")
    assert envoyes == []


def test_refus_traduit_en_anglais(envoyes, monkeypatch):
    monkeypatch.setenv("MA3IA_LANGUE", "en")
    assert tools.create_macro(3, "A", ['a"b']).startswith("Error: double quotes are not allowed")
    assert envoyes == []


def test_generation_refuse_toujours_les_guillemets(envoyes):
    r = tools.generate_macros_from_template(start_macro=1, line_templates=['Set "x"'], delai_ms=0)
    assert r.startswith("Erreur : guillemets doubles interdits")
    assert envoyes == []
