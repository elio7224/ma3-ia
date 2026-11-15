"""Mode validation : l'IA prépare, l'utilisateur envoie ou annule (sans console ni vraie API)."""
from types import SimpleNamespace

import pytest

import journal
import ma3
import reglages
import tools


@pytest.fixture
def appli(tmp_path, monkeypatch):
    monkeypatch.setenv("MA3IA_CONFIG_DIR", str(tmp_path / "cfg"))
    import app
    app.COUT_SESSION["usd"] = 0.0
    app.EN_ATTENTE.clear()
    monkeypatch.setattr(app, "DELAI_ENVOI_S", 0)
    monkeypatch.setattr(app.time, "sleep", lambda s: None)
    monkeypatch.setattr(tools.time, "sleep", lambda s: None)
    tools._derniere_sauvegarde[0] = 0.0
    envoyes = []
    client = ma3.MA3("127.0.0.1", 9)
    monkeypatch.setattr(client, "client", SimpleNamespace(send_message=lambda adr, c: envoyes.append(c)))
    monkeypatch.setattr(tools, "ma3", client)
    usage = SimpleNamespace(input_tokens=10, output_tokens=0, cache_read_input_tokens=0, cache_creation_input_tokens=0)
    reponses = [
        SimpleNamespace(stop_reason="tool_use", usage=usage, content=[SimpleNamespace(
            type="tool_use", id="t1", name="run_command", input={"cmd": "Delete Macro 1 Thru 5 /NoConfirmation"})]),
        SimpleNamespace(stop_reason="end_turn", usage=usage, content=[SimpleNamespace(type="text", text="prêt")]),
    ]
    monkeypatch.setattr(app, "obtenir_client", lambda: SimpleNamespace(messages=SimpleNamespace(create=lambda **k: reponses.pop(0))))
    monkeypatch.setattr(app, "sauvegarder_memoire_disque", lambda m: None)
    return app, envoyes


def _demander(app):
    return app.chat(app.ChatPayload(messages=[{"role": "user", "content": "supprime les macros 1 à 5"}], modele="haiku"))


def test_capture_n_envoie_rien():
    envoyes = []
    client = ma3.MA3("127.0.0.1", 9)
    client.client = SimpleNamespace(send_message=lambda adr, c: envoyes.append(c))
    with ma3.capture() as cmds:
        client.send("ClearAll")
    assert cmds == ["ClearAll"] and envoyes == [] and not ma3.en_capture()


def test_mode_validation_prepare_puis_envoie(appli):
    app, envoyes = appli
    reglages.enregistrer({"validation_manuelle": True})
    r = _demander(app)
    assert envoyes == [] and len(r["en_attente"]) == 1
    lot = r["en_attente"][0]
    assert lot["commandes"] == ["SaveShow", "Delete Macro 1 Thru 5 /NoConfirmation"]   # sauvegarde en premier
    assert "MODE VALIDATION" in r["actions"][0]["result"]
    assert app.envoyer_attente(lot["id"])["ok"]
    assert envoyes == lot["commandes"]
    assert journal.lire()[0]["source"].startswith("Validé · run_command")
    assert not app.envoyer_attente(lot["id"])["ok"]                                    # déjà envoyé


def test_annuler(appli):
    app, envoyes = appli
    reglages.enregistrer({"validation_manuelle": True})
    lot = _demander(app)["en_attente"][0]
    app.annuler_attente(lot["id"])
    assert not app.envoyer_attente(lot["id"])["ok"] and envoyes == []


def test_sans_validation_envoi_direct(appli):
    app, envoyes = appli
    r = _demander(app)
    assert r["en_attente"] == [] and envoyes == ["SaveShow", "Delete Macro 1 Thru 5 /NoConfirmation"]
