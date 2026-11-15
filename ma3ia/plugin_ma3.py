"""Installation automatique du plugin AI_Index dans grandMA3.

Le plugin (plugin/ai_index.lua) liste les objets du show dans gma3_library/ai_index.json, que l'IA lit ensuite.
Installation ou mise à jour, sans jamais créer de doublon :
  1. on lance le plugin : s'il répond avec la version attendue (champ "plugin" de l'index) → rien à faire ;
     s'il répond avec une version plus ancienne → on le supprime (Delete Plugin "AI_Index") et on continue ;
  2. sinon on écrit ai_index.xml dans gma3_library/datapools/plugins, au format d'export de grandMA3
     (UserPlugin > ComponentLua > FileContent : le Lua en Base64, par blocs de 1024 octets) ;
  3. on envoie `Import Plugin Library "ai_index.xml" At Plugin <n>` (réglage « plugin_emplacement ») :
     testé sur grandMA3 onPC 2.5, sans « At Plugin <n> » la console répond « Failed » ;
  4. on relance le plugin pour vérifier que l'index arrive.
OSC est à sens unique : seule l'étape 4 prouve que l'import a marché.
"""
import base64
import os
import shutil
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
VERSION_ATTENDUE = 2                            # = VERSION_PLUGIN dans plugin/ai_index.lua


def version_dans_index():
    """Version du plugin qui a écrit ai_index.json (1 si le champ manque), None si pas d'index lisible."""
    import json
    try:
        with open(tools._fichier_index(), encoding="utf-8-sig", errors="replace") as f:
            return json.load(f).get("plugin", 1)
    except (OSError, ValueError):
        return None


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
        mise_a_jour = False
        if tools._lancer_plugin_index() is None:
            version = version_dans_index()
            if version is not None and version >= VERSION_ATTENDUE:
                etapes.append(tr(f"✅ Le plugin répond (version {version}) : il est déjà installé et à jour.",
                                 f"✅ The plugin answers (version {version}): already installed and up to date."))
                return {"ok": True, "deja_installe": True, "etapes": etapes, "chemin_xml": None,
                        "message": tr("Le plugin AI_Index est déjà installé, à jour, et fonctionne.",
                                      "The AI_Index plugin is already installed, up to date and working.")}
            mise_a_jour = True
            etapes.append(tr(f"Le plugin répond en version {version}, la version {VERSION_ATTENDUE} est disponible : mise à jour.",
                             f"The plugin answers with version {version}, version {VERSION_ATTENDUE} is available: updating."))
            tools.ma3.send(f'Delete Plugin "{NOM_PLUGIN}" /NoConfirmation')
            etapes.append(tr(f'Ancienne version supprimée : Delete Plugin "{NOM_PLUGIN}" /NoConfirmation',
                             f'Old version deleted: Delete Plugin "{NOM_PLUGIN}" /NoConfirmation'))
        else:
            etapes.append(tr("Pas de réponse : le plugin n'est pas (encore) dans le show (« Object not found » sur la console : normal).",
               "No answer: the plugin is not in the show yet (\"Object not found\" on the console: normal)."))

        # 2. Fichier d'import dans la bibliothèque de la console
        bib = reglages.charger()["dossier_bibliotheque"]
        dossier = os.path.join(bib, "datapools", "plugins")
        chemin_xml = os.path.join(dossier, FICHIER_XML)
        try:
            # Garde une copie d'un éventuel ai_index.xml différent (ex : export fait depuis la console).
            if os.path.isfile(chemin_xml):
                shutil.copy2(chemin_xml, chemin_xml + ".bak")
                etapes.append(tr(f"Ancien fichier gardé : {chemin_xml}.bak", f"Old file kept: {chemin_xml}.bak"))
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
        emplacement = reglages.charger()["plugin_emplacement"]
        commande = f'Import Plugin Library "{FICHIER_XML}" At Plugin {emplacement}'
        tools.ma3.send(commande)
        etapes.append(tr(f"Commande envoyée : {commande}", f"Command sent: {commande}"))
        time.sleep(PAUSE_APRES_IMPORT_S)

        # 4. Vérification
        etapes.append(tr("Vérification : nouveau lancement du plugin…", "Check: running the plugin again…"))
        erreur = tools._lancer_plugin_index()
    if erreur is None and (version_dans_index() or 0) >= VERSION_ATTENDUE:
        etapes.append(tr("✅ L'index est arrivé avec la bonne version : le plugin est installé.",
                         "✅ The index arrived with the right version: the plugin is installed."))
        return {"ok": True, "deja_installe": False, "mis_a_jour": mise_a_jour, "etapes": etapes, "chemin_xml": chemin_xml,
                "message": (tr("Plugin AI_Index mis à jour dans ton show. Enregistre le show pour le garder.",
                               "AI_Index plugin updated in your show. Save the show to keep it.") if mise_a_jour else
                            tr("Plugin AI_Index installé dans ton show. Enregistre le show pour le garder.",
                               "AI_Index plugin installed in your show. Save the show to keep it."))}
    etapes.append(tr("❌ Toujours pas d'index après l'import.", "❌ Still no index after the import."))
    return {"ok": False, "deja_installe": False, "etapes": etapes, "chemin_xml": chemin_xml,
            "message": tr("L'installation n'a pas pu être confirmée. Vérifie que grandMA3 est ouvert, que l'OSC est activé "
                          "et que l'emplacement choisi est vide dans le pool Plugins (sinon choisis-en un autre), "
                          "ou fais l'import à la main (instructions ci-dessous).",
                          "The installation could not be confirmed. Check that grandMA3 is open, that OSC is enabled "
                          "and that the chosen slot is empty in the Plugins pool (otherwise pick another one), "
                          "or import it by hand (instructions below).")}
