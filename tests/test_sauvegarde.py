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


def test_resultats_traduits_en_anglais(console, monkeypatch):
    monkeypatch.setenv("MA3IA_LANGUE", "en")
    assert tools.create_macro(5, "Test", ["ClearAll"]) == "Macro 5 created (1 lines)."
    assert "Show saved" in tools.run_command("Delete Group 1 Thru 3")
    import ma3
    client = ma3.MA3("127.0.0.1", 9)
    monkeypatch.setattr(client, "client", type("U", (), {"send_message": lambda self, a, c: None})())
    assert client.send("Go+ Sequence 1") == "sent"


@pytest.mark.parametrize("cmd", [
    "Delete Macro 1 + 5 + 9 /NoConfirmation",
    "Delete Sequence *",
    "delete group 1+2",
    "Store Group 5 /Overwrite",
    "Store Preset 4.3 /overwrite /NoConfirmation",
])
def test_autres_commandes_destructrices_sauvegardent(console, cmd):
    r = tools.run_command(cmd)
    assert console == ["SaveShow", cmd] and "Backup Shows" in r


@pytest.mark.parametrize("cmd", [
    "Store Group 5", "Store Macro 3 /Merge", "Label Macro 3 \"Test\"", "Go+ Sequence 1",
    "Delete Macro 3 /NoConfirmation", "ClearAll", "Group 1 + Group 2 At 50",
])
def test_commandes_anodines_sans_sauvegarde(console, cmd):
    tools.run_command(cmd)
    assert console == [cmd]
