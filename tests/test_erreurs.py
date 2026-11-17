"""Cas d'erreur : pas de clé, clé refusée, pas de réseau, crédit épuisé, console éteinte. Messages clairs, en fr et en en."""
from types import SimpleNamespace

import anthropic
try:
    import httpx
except ImportError:          # anthropic récent : httpx2
    import httpx2 as httpx
import pytest

import tools


@pytest.fixture
def appli(tmp_path, monkeypatch):
    monkeypatch.setenv("MA3IA_CONFIG_DIR", str(tmp_path / "cfg"))
    import app
    app.COUT_SESSION["usd"] = 0.0
    monkeypatch.setattr(app, "sauvegarder_memoire_disque", lambda m: None)
    return app


def _req():
    return httpx.Request("POST", "https://api.anthropic.com/v1/messages")


def _statut(code, corps="x"):
    return httpx.Response(code, request=_req(), json={"error": {"message": corps}})


def _erreurs(app):
    return {
        "cle": anthropic.AuthenticationError("bad", response=_statut(401), body=None),
        "droit": anthropic.PermissionDeniedError("no", response=_statut(403), body=None),
        "debit": anthropic.RateLimitError("rate", response=_statut(429), body=None),
        "delai": anthropic.APITimeoutError(request=_req()),
        "reseau": anthropic.APIConnectionError(request=_req()),
        "credit": anthropic.BadRequestError("Your credit balance is too low", response=_statut(400), body=None),
        "surcharge": anthropic.APIStatusError("overloaded", response=_statut(529), body=None),
    }


@pytest.mark.parametrize("langue", ["fr", "en"])
def test_messages_api_clairs_et_traduits(appli, monkeypatch, langue):
    monkeypatch.setenv("MA3IA_LANGUE", langue)
    attendu = {
        "fr": {"cle": "Clé API refusée", "droit": "pas le droit", "debit": "Limite de débit", "delai": "pas répondu",
               "reseau": "connexion Internet", "credit": "Crédit Anthropic épuisé", "surcharge": "surchargée"},
        "en": {"cle": "API key rejected", "droit": "not allowed", "debit": "Rate limit", "delai": "did not answer",
               "reseau": "Internet connection", "credit": "credit exhausted", "surcharge": "overloaded"},
    }[langue]
    for nom, e in _erreurs(appli).items():
        msg = appli.message_erreur_api(e)
        assert attendu[nom] in msg, (nom, msg)


def test_erreur_inconnue_garde_le_detail(appli):
    assert "ValueError" in appli.message_erreur_api(ValueError("boum"))


def test_sans_cle_message_clair(appli, monkeypatch):
    monkeypatch.setattr(appli, "obtenir_client", lambda: None)
    r = appli.chat(appli.ChatPayload(messages=[{"role": "user", "content": "salut"}], modele="haiku"))
    assert "Aucune clé API" in r["response"] and "Réglages" in r["response"]


def test_chat_sans_reseau_renvoie_le_message_reseau(appli, monkeypatch):
    def echec(**k):
        raise anthropic.APIConnectionError(request=_req())
    monkeypatch.setattr(appli, "obtenir_client", lambda: SimpleNamespace(messages=SimpleNamespace(create=echec)))
    r = appli.chat(appli.ChatPayload(messages=[{"role": "user", "content": "salut"}], modele="haiku"))
    assert "connexion Internet" in r["response"]


def test_cle_au_mauvais_format_refusee_sans_appel_reseau():
    import reglages
    ok, msg = reglages.tester_cle("pas-une-cle")
    assert not ok and "sk-ant-" in msg


def test_test_cle_sans_reseau(monkeypatch):
    import reglages

    class Faux:
        def __init__(self, **k): pass
        @property
        def models(self):
            def lister(limit=1): raise anthropic.APIConnectionError(request=_req())
            return SimpleNamespace(list=lister)
    monkeypatch.setattr(anthropic, "Anthropic", Faux)
    ok, msg = reglages.tester_cle("sk-ant-" + "x" * 30)
    assert not ok and "Internet" in msg


def test_osc_mauvais_port_et_hote_inconnu():
    import reglages
    ok, msg = reglages.tester_osc("127.0.0.1", 99999)
    assert not ok and msg
    ok, msg = reglages.tester_osc("hote.inexistant.invalid", 8000)
    assert not ok and ("introuvable" in msg or "not found" in msg)


def test_console_eteinte_message_du_plugin(bibliotheque_factice, monkeypatch):
    """Aucun fichier d'index n'apparaît (console éteinte / mauvais port) : le message dit quoi vérifier."""
    import ma3
    envoyes = []
    client = ma3.MA3("127.0.0.1", 9)
    monkeypatch.setattr(client, "client", SimpleNamespace(send_message=lambda a, c: envoyes.append(c)))
    monkeypatch.setattr(tools, "ma3", client)
    monkeypatch.setattr(tools, "DELAI_MAX_PLUGIN", 0.3)
    monkeypatch.setattr(tools.time, "sleep", lambda s: None)
    t = iter(range(0, 1000))
    monkeypatch.setattr(tools.time, "time", lambda: next(t))
    msg = tools._lancer_plugin_index()
    assert envoyes and "OSC" in msg and "AI_Index" in msg
