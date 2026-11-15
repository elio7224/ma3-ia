"""Journal des commandes et garde-fou de coût, testés sans console ni vraie API."""
from types import SimpleNamespace

import pytest

import journal
import reglages


@pytest.fixture(autouse=True)
def isole(tmp_path, monkeypatch):
    monkeypatch.setenv("MA3IA_CONFIG_DIR", str(tmp_path / "cfg"))


# ---------------------------------------------------------------- journal

def test_journal_note_lit_et_efface():
    journal.noter("ClearAll", "127.0.0.1:8000")
    with journal.source("IA · create_macro"):
        journal.noter("Store Macro 5")
    journal.noter("Go+ Macro 5")
    e = journal.lire()
    assert [x["commande"] for x in e] == ["Go+ Macro 5", "Store Macro 5", "ClearAll"]   # plus récent d'abord
    assert e[1]["source"] == "IA · create_macro" and e[0]["source"] == "App"
    assert e[2]["cible"] == "127.0.0.1:8000" and len(e[0]["heure"]) == 19
    journal.effacer()
    assert journal.lire() == []


def test_journal_elague(monkeypatch):
    monkeypatch.setattr(journal, "MAX_LIGNES", 3)
    for i in range(10):
        journal.noter(f"cmd {i}")
    with open(journal.fichier_journal(), encoding="utf-8") as f:
        assert len(f.readlines()) < 10                     # les plus anciennes lignes ont été supprimées
    assert [x["commande"] for x in journal.lire(3)] == ["cmd 9", "cmd 8", "cmd 7"]


def test_ma3_send_journalise(monkeypatch):
    import ma3
    envoyes = []
    client = ma3.MA3("127.0.0.1", 9999)
    monkeypatch.setattr(client, "client", SimpleNamespace(send_message=lambda adr, cmd: envoyes.append(cmd)))
    client.send("Go+ Sequence 1")
    assert envoyes == ["Go+ Sequence 1"] and journal.lire()[0]["commande"] == "Go+ Sequence 1"


# ---------------------------------------------------------------- plafond

def test_plafond_validation():
    r, err = reglages.enregistrer({"plafond_session_usd": "2,5"})
    assert not err and r["plafond_session_usd"] == 2.5
    assert reglages.enregistrer({"plafond_session_usd": "-1"})[1]
    assert reglages.enregistrer({"plafond_session_usd": "beaucoup"})[1]
    assert reglages.charger()["plafond_session_usd"] == 2.5


def _reponse(texte=None, outil=None, entree=1_000_000):
    """Fausse réponse API. 1 M tokens d'entrée Haiku = 0,10 $."""
    contenu = []
    if texte:
        contenu.append(SimpleNamespace(type="text", text=texte))
    if outil:
        contenu.append(SimpleNamespace(type="tool_use", id="t1", name=outil, input={"cmd": "ClearAll"}))
    usage = SimpleNamespace(input_tokens=entree, output_tokens=0, cache_read_input_tokens=0, cache_creation_input_tokens=0)
    return SimpleNamespace(content=contenu, usage=usage, stop_reason="tool_use" if outil else "end_turn")


@pytest.fixture
def appli(monkeypatch):
    import app
    app.COUT_SESSION["usd"] = 0.0
    reponses = []
    faux = SimpleNamespace(messages=SimpleNamespace(create=lambda **k: reponses.pop(0)))
    monkeypatch.setattr(app, "obtenir_client", lambda: faux)
    monkeypatch.setattr(app, "sauvegarder_memoire_disque", lambda m: None)
    envoyes = []
    monkeypatch.setitem(app.FUNCS, "run_command", lambda cmd: (envoyes.append(cmd), journal.noter(cmd))[1] or "envoyé")
    return app, reponses, envoyes


def _demander(app, texte="salut"):
    return app.chat(app.ChatPayload(messages=[{"role": "user", "content": texte}], modele="haiku"))


def test_cout_cumule_alerte_puis_blocage(appli):
    app, reponses, _ = appli
    reglages.enregistrer({"plafond_session_usd": 0.25})
    reponses += [_reponse("ok"), _reponse("ok")]
    r = _demander(app)
    assert r["session"]["cout_usd"] == pytest.approx(0.10) and not r["session"]["alerte"]
    r = _demander(app)
    assert r["session"]["cout_usd"] == pytest.approx(0.20) and r["session"]["alerte"] and not r["session"]["atteint"]
    app.COUT_SESSION["usd"] = 0.25
    r = _demander(app)
    assert "Plafond de dépense atteint" in r["response"] and r["session"]["atteint"]
    assert app.reinitialiser_session()["cout_usd"] == 0


def test_arret_avant_les_actions_si_plafond_atteint(appli):
    app, reponses, envoyes = appli
    reglages.enregistrer({"plafond_session_usd": 0.05})
    reponses += [_reponse(outil="run_command")]        # 0,10 $ : dépasse le plafond avant l'action
    r = _demander(app)
    assert envoyes == [] and "pendant la demande" in r["response"]


def test_outil_ia_journalise_avec_source(appli):
    app, reponses, envoyes = appli
    reglages.enregistrer({"plafond_session_usd": 0})   # pas de plafond
    reponses += [_reponse(outil="run_command", entree=10), _reponse("fait", entree=10)]
    r = _demander(app)
    assert envoyes == ["ClearAll"] and r["response"] == "fait"
    assert journal.lire()[0]["source"] == "IA · run_command"


# ---------------------------------------------------------------- langue

def test_langue_reglage_et_traductions(monkeypatch):
    import i18n
    monkeypatch.delenv("MA3IA_LANGUE")
    assert reglages.enregistrer({"langue": "en"})[0]["langue"] == "en"
    assert i18n.langue() == "en"
    assert reglages.enregistrer_cle("pas une clé")[1].startswith("Invalid key")
    reglages.enregistrer({"langue": "fr"})
    assert reglages.enregistrer_cle("pas une clé")[1].startswith("Clé invalide")
    assert reglages.enregistrer({"langue": "de"})[1]                     # langue inconnue refusée
    reglages.enregistrer({"langue": "auto"})
    assert i18n.langue() == i18n.langue_systeme() in ("fr", "en")


def test_message_plafond_en_anglais(appli, monkeypatch):
    app, reponses, _ = appli
    monkeypatch.setenv("MA3IA_LANGUE", "en")
    reglages.enregistrer({"plafond_session_usd": 0.1})
    app.COUT_SESSION["usd"] = 0.2
    assert "Spending limit reached" in _demander(app)["response"]
