"""Installation automatique du plugin AI_Index dans grandMA3.

Le plugin (plugin/ai_index.lua) liste les objets du show dans gma3_library/ai_index.json, que l'IA lit ensuite.
Installation, sans jamais créer de doublon :
  1. on lance le plugin : s'il répond, il est déjà installé → on s'arrête ;
  2. sinon on écrit ai_index.xml dans gma3_library/datapools/plugins, au format d'export de grandMA3
     (UserPlugin > ComponentLua > FileContent : le Lua en Base64, par blocs de 1024 octets) ;
  3. on envoie `Import Plugin Library "ai_index.xml"` (manuel 2.5, mot-clé Import) ;
  4. on relance le plugin pour vérifier que l'index arrive.
OSC est à sens unique : seule l'étape 4 prouve que l'import a marché.
"""
import base64
import os
import time

import journal
import reglages
import tools
from i18n import tr

NOM_PLUGIN = "AI_Index"
FICHIER_XML = reglages.PLUGIN_FICHIER          # ai_index.xml
TAILLE_BLOC = 1024
DATA_VERSION = "2.5.1.0"                        # identique à un export réel de grandMA3 2.5
PAUSE_APRES_IMPORT_S = 2.0


def generer_xml(lua: bytes, version: str = "0.0.0.0") -> str:
    """Fichier d'export de plugin grandMA3 contenant le code Lua."""
    blocs = [lua[i:i + TAILLE_BLOC] for i in range(0, len(lua), TAILLE_BLOC)] or [b""]
    lignes = "\n".join(f'                <Block Base64="{base64.b64encode(b).decode("ascii")}"/>' for b in blocs)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<GMA3 DataVersion="{DATA_VERSION}">\n'
            f'    <UserPlugin Name="{NOM_PLUGIN}" Version="{version}">\n'
            '        <ComponentLua>\n'
            f'            <FileContent Size="{len(blocs)}">\n{lignes}\n'
            '            </FileContent>\n'
            '        </ComponentLua>\n'
            '    </UserPlugin>\n'
            '</GMA3>\n')


def _version_plugin() -> str:
    try:
        from version import VERSION
        return ".".join((VERSION.split(".") + ["0"] * 4)[:4])
    except Exception:
        return "0.0.0.0"


def installer() -> dict:
    """Installe le plugin si besoin. Renvoie {ok, deja_installe, etapes, message, chemin_xml}."""
    etapes = []
    with journal.source("Installation du plugin"):
        # 1. Déjà installé ?
        etapes.append(tr("Test : lancement du plugin AI_Index déjà présent dans le show…",
                         "Test: running the AI_Index plugin already in the show…"))
        if tools._lancer_plugin_index() is None:
            etapes.append(tr("✅ Le plugin répond : il est déjà installé, rien à importer.",
                             "✅ The plugin answers: it is already installed, nothing to import."))
            return {"ok": True, "deja_installe": True, "etapes": etapes, "chemin_xml": None,
                    "message": tr("Le plugin AI_Index est déjà installé et fonctionne.",
                                  "The AI_Index plugin is already installed and working.")}
        etapes.append(tr("Pas de réponse : le plugin n'est pas (encore) dans le show.",
                         "No answer: the plugin is not in the show (yet)."))

        # 2. Fichier d'import dans la bibliothèque de la console
        bib = reglages.charger()["dossier_bibliotheque"]
        dossier = os.path.join(bib, "datapools", "plugins")
        chemin_xml = os.path.join(dossier, FICHIER_XML)
        try:
            with open(reglages.chemin_plugin_lua(), "rb") as f:
                lua = f.read()
            os.makedirs(dossier, exist_ok=True)
            with open(chemin_xml, "w", encoding="utf-8-sig", newline="\n") as f:
                f.write(generer_xml(lua, _version_plugin()))
        except OSError as e:
            etapes.append(tr(f"❌ Impossible d'écrire {chemin_xml} : {e}", f"❌ Cannot write {chemin_xml}: {e}"))
            return {"ok": False, "deja_installe": False, "etapes": etapes, "chemin_xml": chemin_xml,
                    "message": tr("Écriture du fichier du plugin impossible : vérifie le dossier gma3_library.",
                                  "Cannot write the plugin file: check the gma3_library folder.")}
        etapes.append(tr(f"Fichier écrit : {chemin_xml}", f"File written: {chemin_xml}"))

        # 3. Import dans le show
        tools.ma3.send(f'Import Plugin Library "{FICHIER_XML}"')
        etapes.append(tr(f'Commande envoyée : Import Plugin Library "{FICHIER_XML}"',
                         f'Command sent: Import Plugin Library "{FICHIER_XML}"'))
        time.sleep(PAUSE_APRES_IMPORT_S)

        # 4. Vérification
        etapes.append(tr("Vérification : nouveau lancement du plugin…", "Check: running the plugin again…"))
        erreur = tools._lancer_plugin_index()
    if erreur is None:
        etapes.append(tr("✅ L'index est arrivé : le plugin est installé.", "✅ The index arrived: the plugin is installed."))
        return {"ok": True, "deja_installe": False, "etapes": etapes, "chemin_xml": chemin_xml,
                "message": tr("Plugin AI_Index installé dans ton show. Enregistre le show pour le garder.",
                              "AI_Index plugin installed in your show. Save the show to keep it.")}
    etapes.append(tr("❌ Toujours pas d'index après l'import.", "❌ Still no index after the import."))
    return {"ok": False, "deja_installe": False, "etapes": etapes, "chemin_xml": chemin_xml,
            "message": tr("L'installation n'a pas pu être confirmée. Vérifie que grandMA3 est ouvert et que l'OSC est activé, "
                          "regarde le pool Plugins, ou fais l'import à la main (instructions ci-dessous).",
                          "The installation could not be confirmed. Check that grandMA3 is open and OSC is enabled, "
                          "look at the Plugins pool, or import it by hand (instructions below).")}
