"""Tests de la couche de réglages : sans console grandMA3, sans vraie clé, sans toucher au vrai coffre Windows."""
import json
import os

import pytest

import reglages

CLE_FAUSSE = "sk-ant-api03-FAUSSE-CLE-POUR-TESTS-0123456789abcd"


@pytest.fixture(autouse=True)
def isole(tmp_path, monkeypatch):
    monkeypatch.setenv("MA3IA_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(reglages, "FICHIER_CLE_LEGACY", str(tmp_path / "absent.txt"))
    coffre = {}
    monkeypatch.setattr(reglages, "_coffre_lire", lambda: coffre.get("k"))
    monkeypatch.setattr(reglages, "_coffre_ecrire", lambda c: coffre.__setitem__("k", c))
    monkeypatch.setattr(reglages, "_coffre_supprimer", lambda: coffre.pop("k", None))
    return coffre


def test_defauts_sans_fichier():
    r = reglages.charger()
    assert r["osc_port"] == 8000 and r["osc_hote"] == "127.0.0.1"
    assert r["modele_defaut"] == "haiku" and r["premier_lancement_fait"] is False


def test_enregistrer_et_recharger():
    r, err = reglages.enregistrer({"osc_hote": "192.168.1.20", "osc_port": "9000", "theme": "clair"})
    assert err == {} and r["osc_port"] == 9000
    assert reglages.charger()["osc_hote"] == "192.168.1.20"
    assert os.path.isfile(reglages.fichier_reglages())


@pytest.mark.parametrize("modif", [{"osc_port": 0}, {"osc_port": 70000}, {"osc_port": "abc"}, {"modele_defaut": "gpt"},
                                   {"theme": "rose"}, {"max_tours_outils": 0}, {"osc_hote": "a b"}, {"inconnu": 1}])
def test_valeurs_invalides_refusees(modif):
    avant = reglages.charger()
    r, err = reglages.enregistrer(modif)
    assert err and r == avant
    assert not os.path.exists(reglages.fichier_reglages())


def test_fichier_corrompu_ou_valeur_invalide_ignores():
    os.makedirs(reglages.dossier_config())
    with open(reglages.fichier_reglages(), "w", encoding="utf-8") as f:
        f.write("{pas du json")
    assert reglages.charger()["osc_port"] == 8000
    with open(reglages.fichier_reglages(), "w", encoding="utf-8") as f:
        json.dump({"osc_port": 99999, "theme": "clair"}, f)
    r = reglages.charger()
    assert r["osc_port"] == 8000 and r["theme"] == "clair"


def test_cle_jamais_dans_le_fichier_de_reglages():
    ok, _ = reglages.enregistrer_cle(CLE_FAUSSE)
    reglages.enregistrer({"theme": "clair"})
    assert ok
    with open(reglages.fichier_reglages(), encoding="utf-8") as f:
        assert "sk-ant" not in f.read()


def test_cle_cycle_coffre():
    assert reglages.etat_cle()["presente"] is False
    assert reglages.enregistrer_cle("pas-une-cle")[0] is False
    assert reglages.enregistrer_cle(CLE_FAUSSE)[0] is True
    etat = reglages.etat_cle()
    assert etat["presente"] and etat["source"] == "coffre"
    assert CLE_FAUSSE not in json.dumps(etat) and etat["masque"].endswith(CLE_FAUSSE[-4:])
    assert reglages.supprimer_cle()[0] is True
    assert reglages.etat_cle()["presente"] is False


def test_repli_variable_environnement_puis_priorite_coffre(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", CLE_FAUSSE)
    assert reglages.trouver_cle() == (CLE_FAUSSE, "variable")
    autre = CLE_FAUSSE.replace("FAUSSE", "AUTRE-")
    reglages.enregistrer_cle(autre)
    assert reglages.trouver_cle() == (autre, "coffre")


def test_repli_ancien_fichier(tmp_path, monkeypatch):
    f = tmp_path / "ancienne.txt"
    f.write_text(CLE_FAUSSE, encoding="utf-8")
    monkeypatch.setattr(reglages, "FICHIER_CLE_LEGACY", str(f))
    assert reglages.trouver_cle() == (CLE_FAUSSE, "fichier")


def test_masquer():
    assert reglages.masquer("") == ""
    assert reglages.masquer(CLE_FAUSSE) == "sk-ant-…" + CLE_FAUSSE[-4:]
    assert CLE_FAUSSE[10:-4] not in reglages.masquer(CLE_FAUSSE)


def test_tester_cle_sans_cle_ne_contacte_pas_l_api():
    ok, msg = reglages.tester_cle()
    assert ok is False and "sk-ant-" in msg


def test_tester_osc_valide_les_entrees():
    assert reglages.tester_osc("127.0.0.1", "x")[0] is False
    assert reglages.tester_osc("", 8000)[0] is False


def test_tester_osc_envoie_un_message(monkeypatch):
    envoyes = []

    class Faux:
        def __init__(self, h, p):
            envoyes.append((h, p))

        def send_message(self, adr, val):
            envoyes.append((adr, val))

    import pythonosc.udp_client
    monkeypatch.setattr(pythonosc.udp_client, "SimpleUDPClient", Faux)
    ok, msg = reglages.tester_osc("127.0.0.1", 8000)
    assert ok and envoyes[0] == ("127.0.0.1", 8000) and envoyes[1][0] == "/cmd"
    assert "pas de réponse" in msg or "ne répond pas" in msg   # honnêteté : OSC à sens unique


def test_verifier_plugin(tmp_path):
    bib = tmp_path / "gma3_library"
    assert reglages.verifier_plugin(str(bib))["bibliotheque_ok"] is False
    (bib / "datapools" / "plugins").mkdir(parents=True)
    (bib / "datapools" / "plugins" / "ai_index.xml").write_text("<x/>")
    (bib / "ai_index.json").write_text("{}")
    r = reglages.verifier_plugin(str(bib))
    assert r["bibliotheque_ok"] and r["plugin_ok"] and r["index_ok"] and r["index_age_min"] == 0
    # Chemin collé avec « Copier en tant que chemin d'accès » (guillemets + espaces)
    r = reglages.verifier_plugin(f'  "{bib}"  ')
    assert r["bibliotheque_ok"] and r["plugin_ok"] and r["bibliotheque"] == os.path.normpath(str(bib))


def test_dossiers_temp_et_application_aux_outils(tmp_path):
    import tools
    bib = str(tmp_path / "lib")
    d = reglages.dossiers_temp(bib)
    assert d[0].endswith(os.path.join("datapools", "groups", "Temp")) and d[-1].endswith(os.path.join("appearances", "Temp"))
    ancien = list(tools.DOSSIERS_TEMP_MA3)
    ancien_client = tools.ma3
    try:
        tools.appliquer_reglages("10.0.0.5", 9001, bib)
        assert tools._fichier_index() == os.path.join(bib, "ai_index.json")
        assert tools.ma3 is not ancien_client
    finally:
        tools.DOSSIERS_TEMP_MA3[:] = ancien
        tools.ma3 = ancien_client


def test_effacer_historique(tmp_path, monkeypatch):
    f = tmp_path / "h.json"
    f.write_text('[{"role":"user","content":"x"}]')
    monkeypatch.setenv("MA3IA_HISTORIQUE", str(f))
    assert "effacé" in reglages.effacer_historique()
    assert json.loads(f.read_text()) == []
