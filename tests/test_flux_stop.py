"""Flux d'événements (/api/chat/flux) et bouton Stop, sans console ni vraie API."""
import json
import threading
from types import SimpleNamespace

import pytest

import ma3
import tools


def _appel(ident, cmd):
    return SimpleNamespace(type="tool_use", id=ident, name="run_command", input={"cmd": cmd})


@pytest.fixture
def appli(tmp_path, monkeypatch):
    monkeypatch.setenv("MA3IA_CONFIG_DIR", str(tmp_path / "cfg"))
    import app
    app.COUT_SESSION["usd"] = 0.0
    app.ANNULATIONS.clear()
    monkeypatch.setattr(tools.time, "sleep", lambda s: None)
    envoyes = []
    client = ma3.MA3("127.0.0.1", 9)
    monkeypatch.setattr(client, "client", SimpleNamespace(send_message=lambda adr, c: envoyes.append(c)))
    monkeypatch.setattr(tools, "ma3", client)
    usage = SimpleNamespace(input_tokens=10, output_tokens=0, cache_read_input_tokens=0, cache_creation_input_tokens=0)
    reponses = [
        SimpleNamespace(stop_reason="tool_use", usage=usage, content=[_appel("t1", "Go+ Sequence 1"), _appel("t2", "Go+ Sequence 2")]),
        SimpleNamespace(stop_reason="end_turn", usage=usage, content=[SimpleNamespace(type="text", text="fini")]),
    ]
    monkeypatch.setattr(app, "obtenir_client", lambda: SimpleNamespace(messages=SimpleNamespace(create=lambda **k: reponses.pop(0))))
    monkeypatch.setattr(app, "sauvegarder_memoire_disque", lambda m: None)
    from reglages import enregistrer
    enregistrer({"validation_manuelle": False})
    return app, envoyes


def _payload(app, ident=""):
    return app.ChatPayload(messages=[{"role": "user", "content": "go"}], modele="haiku", ident=ident)


def _lire_flux(reponse):
    async def tout():
        return [json.loads(l) async for l in reponse.body_iterator]
    import asyncio
    return asyncio.run(tout())


def test_le_flux_emet_tour_actions_puis_final(appli):
    app, envoyes = appli
    evts = _lire_flux(app.chat_flux(_payload(app, "abc")))
    types = [e["type"] for e in evts]
    assert types == ["tour", "action", "action", "tour", "final"]
    assert evts[1]["action"]["name"] == "run_command"
    assert evts[-1]["data"]["response"] == "fini" and envoyes == ["Go+ Sequence 1", "Go+ Sequence 2"]
    assert app.ANNULATIONS == {}                      # nettoyé à la fin


def test_stop_entre_deux_outils(appli):
    app, envoyes = appli
    ev = threading.Event()
    gen = app._executer_chat(_payload(app), ev)
    vus = []
    try:
        while True:
            e = next(gen)
            vus.append(e["type"])
            if e["type"] == "action":
                ev.set()                              # l'utilisateur clique sur Stop après la 1re action
    except StopIteration as fin:
        final = fin.value
    assert envoyes == ["Go+ Sequence 1"]              # la 2e commande n'est pas partie
    assert "Arrêté" in final["response"] and vus.count("action") == 1


def test_stop_avant_le_premier_tour(appli):
    app, envoyes = appli
    ev = threading.Event()
    ev.set()
    gen = app._executer_chat(_payload(app), ev)
    with pytest.raises(StopIteration) as fin:
        next(gen)
    assert "Arrêté" in fin.value.value["response"] and envoyes == []


def test_endpoint_stop(appli):
    app, _ = appli
    assert app.chat_stop(app.StopPayload(ident="inconnu")) == {"ok": False}
    ev = app.ANNULATIONS["x"] = threading.Event()
    assert app.chat_stop(app.StopPayload(ident="x")) == {"ok": True} and ev.is_set()


def test_chat_sans_flux_inchange(appli):
    app, envoyes = appli
    d = app.chat(_payload(app))
    assert d["response"] == "fini" and len(d["actions"]) == 2


def test_flux_en_http(appli):
    """Test de bout en bout par HTTP : chaque ligne reçue est un JSON, la dernière est le résultat final."""
    from fastapi.testclient import TestClient
    app, envoyes = appli
    with TestClient(app.app) as c:
        r = c.post("/api/chat/flux", json={"messages": [{"role": "user", "content": "go"}], "modele": "haiku", "ident": "h1"})
    assert r.status_code == 200 and "ndjson" in r.headers["content-type"]
    evts = [json.loads(l) for l in r.text.splitlines() if l.strip()]
    assert evts[-1]["type"] == "final" and evts[-1]["data"]["response"] == "fini"
    assert [e["type"] for e in evts].count("action") == 2
