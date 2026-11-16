"""Résumé des actions gardé dans l'historique (sans console ni vraie API)."""
from types import SimpleNamespace

import pytest

import config
import ma3
import reglages
import tools
from tests.test_validation import appli  # noqa: F401  (fixture : app avec faux client IA + faux OSC)


def _app(tmp_path, monkeypatch):
    monkeypatch.setenv("MA3IA_CONFIG_DIR", str(tmp_path / "cfg"))
    import app
    return app


def test_resume_vide(tmp_path, monkeypatch):
    assert _app(tmp_path, monkeypatch).resumer_actions([]) == ""


def test_resume_outil_parametres_resultat_erreur(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    faits = [
        {"name": "run_command", "input": {"cmd": "Go Sequence 1"}, "result": "OK envoyé\nligne 2", "error": False, "attente": None},
        {"name": "lire_xml_temp", "input": {"cible": "macros/9"}, "result": "boom", "error": True, "attente": None},
    ]
    r = app.resumer_actions(faits)
    assert r.startswith("\n\n[ACTIONS]\n") and r.endswith("\n[/ACTIONS]")
    assert 'run_command(cmd="Go Sequence 1") ➔ OK envoyé' in r
    assert "ligne 2" not in r                      # une seule ligne de résultat
    assert "lire_xml_temp(cible=\"macros/9\") ➔ ERREUR : boom" in r


def test_resume_tronque_et_plafonne(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    long = "x" * 5000
    faits = [{"name": "run_command", "input": {"cmd": long}, "result": long, "error": False, "attente": None}
             for _ in range(app.RESUME_MAX_LIGNES + 5)]
    r = app.resumer_actions(faits)
    lignes = r.split("\n")
    assert len([l for l in lignes if l.startswith("- run_command")]) == app.RESUME_MAX_LIGNES
    assert "5 autre(s) action(s)" in r
    assert max(len(l) for l in lignes) < 400
    assert len(r) < 5000


def test_attente_statuts(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch)
    app.EN_ATTENTE.clear(); app.STATUT_ATTENTE.clear()
    app.EN_ATTENTE["aaa"] = {"outil": "run_command", "commandes": []}
    app.STATUT_ATTENTE.update({"bbb": "envoyee", "ccc": "annulee"})
    t = "{#aaa} {#bbb} {#ccc} {#ddd}"
    r = app.resoudre_attentes(t)
    assert "EN ATTENTE" in r and "ENVOYÉES" in r and "ANNULÉES" in r and "inconnu" in r
    assert "{#" not in r


def _tour(app):
    return app.chat(app.ChatPayload(messages=[{"role": "user", "content": "supprime les macros 1 à 5"}], modele="haiku"))


def test_tour_avec_outil_ajoute_le_resume_a_l_historique(appli):  # noqa: F811
    app, envoyes = appli
    res = _tour(app)
    assert "[ACTIONS]" not in res["response"]       # l'interface n'affiche que le texte
    dernier = res["messages"][-1]
    assert dernier["role"] == "assistant" and dernier["content"].startswith("prêt")
    assert "[ACTIONS]" in dernier["content"] and "run_command(" in dernier["content"]
    assert "NON envoyées" not in dernier["content"]  # hors mode validation : envoyé directement
    propres = config.limiter_historique(app.conserver_memoire_texte(res["messages"]))
    assert propres[-1]["content"] == dernier["content"]
    assert all(isinstance(m["content"], str) for m in propres)


@pytest.mark.parametrize("action,attendu", [("envoyer", "ENVOYÉES"), ("annuler", "ANNULÉES"), (None, "toujours EN ATTENTE")])
def test_validation_statut_dans_le_resume(appli, action, attendu):  # noqa: F811
    app, envoyes = appli
    reglages.enregistrer({"validation_manuelle": True})
    res = _tour(app)
    ident = res["en_attente"][0]["id"]
    contenu = res["messages"][-1]["content"]
    assert f"{{#{ident}}}" in contenu and "NON envoyées" in contenu
    if action:
        getattr(app, action + "_attente")(ident)
    assert attendu in app.resoudre_attentes(contenu)
    # le message de résultat de l'outil (préfixe de validation) n'encombre pas le résumé
    assert "MODE VALIDATION" not in contenu
