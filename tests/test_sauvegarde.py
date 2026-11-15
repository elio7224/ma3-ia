"""Sauvegarde automatique du show (SaveShow) avant les actions de masse, sans console."""
import pytest

import reglages
import tools


@pytest.fixture(autouse=True)
def console(tmp_path, monkeypatch):
    monkeypatch.setenv("MA3IA_CONFIG_DIR", str(tmp_path / "cfg"))
    envoyes = []
    monkeypatch.setattr(tools, "ma3", type("Faux", (), {"send": lambda self, c: envoyes.append(c) or "envoyé"})())
    monkeypatch.setattr(tools.time, "sleep", lambda s: None)
    tools._derniere_sauvegarde[0] = 0.0
    return envoyes


def test_commandes_de_masse():
    assert tools.est_commande_de_masse("Delete Macro 1 Thru 50 /NoConfirmation")
    assert tools.est_commande_de_masse("copy group 1 thru 5 at 10")
    assert not tools.est_commande_de_masse("Fixture 1 Thru 10 At 50")
    assert not tools.est_commande_de_masse("Delete Macro 3")


def test_saveshow_avant_une_commande_de_masse(console):
    r = tools.run_command("Delete Macro 1 Thru 50 /NoConfirmation")
    assert console == ["SaveShow", "Delete Macro 1 Thru 50 /NoConfirmation"] and "Backup Shows" in r
    tools.run_command("Go+ Sequence 1")
    assert console[-1] == "Go+ Sequence 1" and console.count("SaveShow") == 1


def test_une_seule_sauvegarde_par_intervalle(console):
    tools.run_command("Delete Group 1 Thru 3")
    r = tools.run_command("Delete Group 4 Thru 6")
    assert console.count("SaveShow") == 1 and "moins de 2 minutes" in r


def test_generation_sauvegarde_mais_pas_l_apercu(console):
    tools.generate_macros_from_template(start_macro=10, line_templates=["Go+ Sequence {macro}"], dry_run=True)
    assert console == []
    tools.generate_macros_from_template(start_macro=10, line_templates=["Go+ Sequence {macro}"])
    assert console[0] == "SaveShow" and len(console) > 1


def test_desactivable(console):
    reglages.enregistrer({"sauvegarde_auto": False})
    r = tools.run_command("Delete Macro 1 Thru 5")
    assert "SaveShow" not in console and "désactivée" in r
    assert reglages.enregistrer({"sauvegarde_auto": "true"})[0]["sauvegarde_auto"] is True
