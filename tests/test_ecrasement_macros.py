"""generate_macros_from_template : refus d'écraser des macros existantes et aperçu obligatoire au-delà de 50."""
import pytest

import tools


@pytest.fixture(autouse=True)
def console(tmp_path, monkeypatch):
    monkeypatch.setenv("MA3IA_CONFIG_DIR", str(tmp_path / "cfg"))
    envoyes = []
    monkeypatch.setattr(tools, "ma3", type("Faux", (), {"send": lambda self, c: envoyes.append(c) or "envoyé"})())
    monkeypatch.setattr(tools.time, "sleep", lambda s: None)
    monkeypatch.setattr(tools, "INDEX_OBJETS", {"macros": {"12": "Ma macro", "13": "Autre"}})
    tools._derniere_sauvegarde[0] = 0.0
    tools._APERCUS_FAITS.clear()
    return envoyes


def _generer(**kw):
    args = dict(start_macro=10, name_template="M{macro}", line_templates=["Go+ Sequence {macro}"],
                loops=[{"var": "g", "start": 1, "count": 5}])
    args.update(kw)
    return tools.generate_macros_from_template(**args)


def test_refuse_d_ecraser_une_macro_existante(console):
    r = _generer()                       # macros 10 à 14 : 12 et 13 existent
    assert r.startswith("Refusé") and "12" in r and "Ma macro" in r
    assert console == []                 # rien envoyé, pas même SaveShow


def test_ecraser_true_envoie(console):
    r = _generer(ecraser=True)
    assert "Succès" in r and "Delete Macro 12 /noconfirm" in console


def test_plage_libre_envoie(console):
    assert "Succès" in _generer(start_macro=100)


def test_apercu_signale_les_numeros_occupes(console):
    r = _generer(dry_run=True)
    assert "ÉCRASÉS" in r and "12" in r and console == []


def test_plus_de_50_exige_un_apercu(console):
    gros = dict(start_macro=200, loops=[{"var": "g", "start": 1, "count": 60}])
    r = _generer(**gros)
    assert r.startswith("Refusé") and "dry_run" in r and console == []
    assert "APERÇU" in _generer(dry_run=True, **gros)
    assert "Succès" in _generer(**gros)


def test_l_apercu_ne_vaut_que_pour_la_meme_demande(console):
    gros = dict(start_macro=200, loops=[{"var": "g", "start": 1, "count": 60}])
    _generer(dry_run=True, **gros)
    autre = dict(gros, start_macro=300)
    assert _generer(**autre).startswith("Refusé")


def test_apercu_perime(console, monkeypatch):
    gros = dict(start_macro=200, loops=[{"var": "g", "start": 1, "count": 60}])
    _generer(dry_run=True, **gros)
    monkeypatch.setattr(tools, "VALIDITE_APERCU_S", -1)
    assert _generer(**gros).startswith("Refusé")


def test_50_macros_ou_moins_sans_apercu(console):
    assert "Succès" in _generer(start_macro=200, loops=[{"var": "g", "start": 1, "count": 50}])
