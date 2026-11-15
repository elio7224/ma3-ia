"""Version du plugin AI_Index : détection d'une ancienne version et mise à jour, sans console."""
import json
import re

import pytest

import plugin_ma3
import reglages
import tools


def test_versions_lua_et_app_identiques():
    with open(reglages.chemin_plugin_lua(), encoding="utf-8") as f:
        lua = f.read()
    assert int(re.search(r"local VERSION_PLUGIN = (\d+)", lua).group(1)) == plugin_ma3.VERSION_ATTENDUE
    assert '"plugin":\' .. VERSION_PLUGIN' in lua


@pytest.fixture
def console(tmp_path, monkeypatch):
    monkeypatch.setenv("MA3IA_CONFIG_DIR", str(tmp_path / "cfg"))
    reglages.enregistrer({"dossier_bibliotheque": str(tmp_path / "lib")})
    envoyes = []
    monkeypatch.setattr(tools, "ma3", type("F", (), {"send": lambda self, c: envoyes.append(c) or "envoyé"})())
    monkeypatch.setattr(plugin_ma3, "PAUSE_APRES_IMPORT_S", 0)
    index = tmp_path / "lib" / "ai_index.json"
    monkeypatch.setattr(tools, "_fichier_index", lambda: str(index))

    def console_repond(*versions):
        """Chaque lancement du plugin écrit un index avec la version suivante (None = pas de réponse)."""
        suite = iter(versions)
        def lancer():
            v = next(suite)
            if v is None:
                return "pas d'index"
            index.parent.mkdir(parents=True, exist_ok=True)
            index.write_text(json.dumps({"version": 1, "pools": []} | ({"plugin": v} if v > 1 else {})), encoding="utf-8")
            return None
        monkeypatch.setattr(tools, "_lancer_plugin_index", lancer)
    return envoyes, console_repond


def test_a_jour_rien_a_faire(console):
    envoyes, repond = console
    repond(plugin_ma3.VERSION_ATTENDUE)
    r = plugin_ma3.installer()
    assert r["ok"] and r["deja_installe"] and envoyes == []


def test_ancienne_version_remplacee(console):
    envoyes, repond = console
    repond(1, plugin_ma3.VERSION_ATTENDUE)          # ancien plugin (sans champ "plugin"), puis le nouveau
    r = plugin_ma3.installer()
    assert r["ok"] and r["mis_a_jour"]
    assert envoyes == ['Delete Plugin "AI_Index" /NoConfirmation', 'Import Plugin Library "ai_index.xml" At Plugin 99']


def test_import_sans_nouvelle_version_signale(console):
    envoyes, repond = console
    repond(1, 1)                                    # l'ancien répond encore après l'import : échec
    assert not plugin_ma3.installer()["ok"]


def test_version_lue_dans_l_index(console, tmp_path):
    _, repond = console
    repond(1)
    tools._lancer_plugin_index()
    tools.charger_contexte_temp()
    assert tools.VERSION_PLUGIN_CONSOLE == 1
