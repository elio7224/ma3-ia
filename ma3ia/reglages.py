"""Couche de réglages de l'application : réglages non secrets (JSON) + clé API (coffre du système).

- Réglages : settings.json dans dossier_config() (dossier modifiable avec la variable MA3IA_CONFIG_DIR) :
  Windows %APPDATA%\\ma3-ia, macOS ~/Library/Application Support/ma3-ia, Linux ~/.config/ma3-ia.
- Clé API : coffre du système via `keyring` (Windows Credential Manager, trousseau macOS) ;
  repli sur ANTHROPIC_API_KEY, puis sur l'ancien cle_api.txt.
- La clé n'est JAMAIS écrite dans settings.json, ni affichée en clair, ni journalisée.
Les fonctions renvoient des dictionnaires / chaînes et ne lèvent pas d'exception vers l'appelant.
"""
import json
import os
import socket
import sys
import time

from config import CLE_FICHIER, MODELE_DEFAUT, MODELES, MAX_TOURS_OUTILS
from i18n import LANGUES, tr

SERVICE_COFFRE = "ma3-ia"
UTILISATEUR_COFFRE = "anthropic_api_key"
FICHIER_CLE_LEGACY = CLE_FICHIER
WINDOWS = sys.platform == "win32"
MAC = sys.platform == "darwin"


def bibliotheque_defaut(plateforme: str = sys.platform) -> str:
    """Dossier gma3_library créé par grandMA3 onPC : C:\\ProgramData sous Windows, ~/MALightingTechnology sous macOS."""
    if plateforme == "win32":
        return r"C:\ProgramData\MALightingTechnology\gma3_library"
    return os.path.join(os.path.expanduser("~"), "MALightingTechnology", "gma3_library")


BIBLIOTHEQUE_DEFAUT = bibliotheque_defaut()
PLUGIN_FICHIER = "ai_index.xml"   # nom du plugin une fois importé dans la console (datapools/plugins)

DEFAUTS = {
    "modele_defaut": MODELE_DEFAUT,
    "osc_hote": "127.0.0.1",
    "osc_port": 8000,
    "dossier_bibliotheque": BIBLIOTHEQUE_DEFAUT,
    "theme": "sombre",
    "max_tours_outils": MAX_TOURS_OUTILS,
    "plafond_session_usd": 1.0,     # 0 = pas de plafond
    "langue": "auto",               # auto (langue de Windows), fr ou en
    "sauvegarde_auto": True,        # SaveShow avant les actions de masse
    "verifier_mises_a_jour": True,  # regarde les Releases GitHub au lancement
    "validation_manuelle": False,   # l'IA prépare, l'utilisateur valide avant l'envoi
    "plugin_emplacement": 99,       # emplacement du pool Plugins pour l'installation d'AI_Index
    "premier_lancement_fait": False,
}
THEMES = ("sombre", "clair")


# ---------------------------------------------------------------- chemins

def dossier_config() -> str:
    base = os.environ.get("MA3IA_CONFIG_DIR")
    if base:
        return base
    maison = os.path.expanduser("~")
    if WINDOWS:
        return os.path.join(os.environ.get("APPDATA") or maison, "ma3-ia")
    if MAC:
        return os.path.join(maison, "Library", "Application Support", "ma3-ia")
    return os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.join(maison, ".config"), "ma3-ia")


def nom_coffre() -> str:
    """Nom du coffre de mots de passe du système, pour les messages."""
    if MAC:
        return tr("trousseau macOS", "macOS Keychain")
    if WINDOWS:
        return tr("coffre Windows", "Windows Credential Manager")
    return tr("coffre du système", "system keyring")


def fichier_reglages() -> str:
    return os.path.join(dossier_config(), "settings.json")


def dossier_ressources() -> str:
    """Dossier du code `ma3ia/` (contient web/, assets/, memo_grandma3.md), ou le bundle PyInstaller."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def chemin_plugin_lua() -> str:
    """Plugin à importer dans la console : `plugin/ai_index.lua` (à la racine du dépôt, ou dans le bundle)."""
    if getattr(sys, "frozen", False):
        return os.path.join(dossier_ressources(), "plugin", "ai_index.lua")
    return os.path.join(os.path.dirname(dossier_ressources()), "plugin", "ai_index.lua")


# ---------------------------------------------------------------- réglages non secrets

def _valider(cle: str, valeur):
    """Renvoie (valeur_nettoyée, None) ou (None, message_d_erreur)."""
    if cle == "modele_defaut":
        return (valeur, None) if valeur in MODELES else (None, tr(f"Modèle inconnu : {valeur!r}.", f"Unknown model: {valeur!r}."))
    if cle == "osc_hote":
        v = str(valeur).strip()
        return (v, None) if v and " " not in v and len(v) <= 253 else (None, tr("Adresse IP / nom d'hôte invalide.", "Invalid IP address / host name."))
    if cle == "osc_port":
        try:
            p = int(valeur)
        except (TypeError, ValueError):
            return None, tr("Le port doit être un nombre.", "The port must be a number.")
        return (p, None) if 1 <= p <= 65535 else (None, tr("Le port doit être entre 1 et 65535.", "The port must be between 1 and 65535."))
    if cle == "dossier_bibliotheque":
        v = str(valeur).strip().strip('"').strip("'").strip()
        return (os.path.expanduser(v), None) if v else (None, tr("Chemin vide.", "Empty path."))
    if cle == "theme":
        return (valeur, None) if valeur in THEMES else (None, tr(f"Thème inconnu : {valeur!r}.", f"Unknown theme: {valeur!r}."))
    if cle == "max_tours_outils":
        try:
            n = int(valeur)
        except (TypeError, ValueError):
            return None, tr("Le nombre de tours doit être un entier.", "The number of rounds must be an integer.")
        return (n, None) if 1 <= n <= 100 else (None, tr("Le nombre de tours doit être entre 1 et 100.", "The number of rounds must be between 1 and 100."))
    if cle == "plafond_session_usd":
        try:
            v = round(float(str(valeur).replace(",", ".").replace("$", "").strip()), 2)
        except (TypeError, ValueError):
            return None, tr("Le plafond doit être un montant en dollars (ex : 1,50).", "The limit must be an amount in dollars (e.g. 1.50).")
        return (v, None) if 0 <= v <= 1000 else (None, tr("Le plafond doit être entre 0 et 1000 $ (0 = aucun plafond).", "The limit must be between 0 and 1000 $ (0 = no limit)."))
    if cle == "plugin_emplacement":
        try:
            n = int(valeur)
        except (TypeError, ValueError):
            return None, tr("L'emplacement du plugin doit être un nombre.", "The plugin slot must be a number.")
        return (n, None) if 1 <= n <= 9999 else (None, tr("L'emplacement du plugin doit être entre 1 et 9999.", "The plugin slot must be between 1 and 9999."))
    if cle == "langue":
        return (valeur, None) if valeur in LANGUES else (None, tr(f"Langue inconnue : {valeur!r}.", f"Unknown language: {valeur!r}."))
    if cle in ("premier_lancement_fait", "sauvegarde_auto", "verifier_mises_a_jour", "validation_manuelle"):
        if isinstance(valeur, str):
            valeur = valeur.strip().lower() in ("1", "true", "oui", "yes", "on")
        return bool(valeur), None
    return None, tr(f"Réglage inconnu : {cle}.", f"Unknown setting: {cle}.")


def charger() -> dict:
    """Réglages courants = défauts + fichier (valeurs invalides ignorées, fichier absent ou corrompu toléré)."""
    r = dict(DEFAUTS)
    try:
        with open(fichier_reglages(), encoding="utf-8") as f:
            brut = json.load(f)
        if isinstance(brut, dict):
            for k, v in brut.items():
                if k in DEFAUTS:
                    val, err = _valider(k, v)
                    if err is None:
                        r[k] = val
    except (OSError, ValueError):
        pass
    return r


def enregistrer(modifs: dict):
    """Applique des modifications partielles. Renvoie (réglages, erreurs) ; rien n'est écrit s'il y a une erreur."""
    erreurs = {}
    propres = {}
    for k, v in (modifs or {}).items():
        val, err = _valider(k, v)
        if err:
            erreurs[k] = err
        else:
            propres[k] = val
    courant = charger()
    if erreurs:
        return courant, erreurs
    courant.update(propres)
    try:
        os.makedirs(dossier_config(), exist_ok=True)
        tmp = fichier_reglages() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(courant, f, ensure_ascii=False, indent=2)
        os.replace(tmp, fichier_reglages())
    except OSError as e:
        return courant, {"_fichier": tr(f"Écriture impossible : {e}", f"Cannot write the file: {e}")}
    return courant, {}


def dossiers_temp(bibliotheque: str) -> list:
    """Dossiers Temp d'export de la console, dans l'ordre attendu par tools.py (le 1er sert à retrouver la bibliothèque)."""
    dp = os.path.join(bibliotheque, "datapools")
    return [os.path.join(dp, s, "Temp") for s in ("groups", "layouts", "macros", "sequences", "presets", "shapes", "matricks")] \
        + [os.path.join(bibliotheque, "appearances", "Temp")]


def chemin_historique() -> str:
    return os.environ.get("MA3IA_HISTORIQUE") or "memoire_chat.json"


def effacer_historique() -> str:
    try:
        with open(chemin_historique(), "w", encoding="utf-8") as f:
            f.write("[]")
        return tr("Historique effacé.", "History cleared.")
    except OSError as e:
        return tr(f"Erreur : {e}", f"Error: {e}")


# ---------------------------------------------------------------- clé API (coffre)

def _coffre_lire():
    try:
        import keyring
        return keyring.get_password(SERVICE_COFFRE, UTILISATEUR_COFFRE)
    except Exception:
        return None


def _coffre_ecrire(cle: str):
    import keyring
    keyring.set_password(SERVICE_COFFRE, UTILISATEUR_COFFRE, cle)


def _coffre_supprimer():
    import keyring
    try:
        keyring.delete_password(SERVICE_COFFRE, UTILISATEUR_COFFRE)
    except keyring.errors.PasswordDeleteError:
        pass


def format_cle_valide(cle) -> bool:
    return isinstance(cle, str) and cle.strip().startswith("sk-ant-") and len(cle.strip()) >= 20


def masquer(cle: str) -> str:
    """Ex. 'sk-ant-…a1b2' : jamais plus de 4 caractères de fin."""
    if not cle:
        return ""
    return "sk-ant-…" + cle[-4:] if len(cle) > 12 else "••••"


def _cle_legacy():
    try:
        with open(FICHIER_CLE_LEGACY, encoding="utf-8-sig") as f:
            c = f.read().strip()
        return c if format_cle_valide(c) else None
    except OSError:
        return None


def trouver_cle():
    """Renvoie (cle, source) ; source ∈ 'coffre' | 'variable' | 'fichier' | None. Ordre : coffre, variable, ancien fichier."""
    c = _coffre_lire()
    if format_cle_valide(c):
        return c.strip(), "coffre"
    c = os.environ.get("ANTHROPIC_API_KEY")
    if format_cle_valide(c):
        return c.strip(), "variable"
    c = _cle_legacy()
    if c:
        return c, "fichier"
    return None, None


def etat_cle() -> dict:
    """État sans secret : {presente, source, masque}."""
    c, source = trouver_cle()
    return {"presente": bool(c), "source": source, "masque": masquer(c) if c else ""}


def enregistrer_cle(cle: str):
    """Renvoie (ok, message). Stocke dans le coffre du système."""
    if not format_cle_valide(cle):
        return False, tr("Clé invalide : elle doit commencer par sk-ant-.", "Invalid key: it must start with sk-ant-.")
    try:
        _coffre_ecrire(cle.strip())
    except Exception as e:
        return False, tr(f"Coffre indisponible ({type(e).__name__}). Utilise la variable ANTHROPIC_API_KEY.", f"{nom_coffre()} unavailable ({type(e).__name__}). Use the ANTHROPIC_API_KEY variable.")
    return True, tr(f"Clé enregistrée dans le {nom_coffre()}.", f"Key saved in {nom_coffre()}.")


def supprimer_cle():
    try:
        _coffre_supprimer()
    except Exception as e:
        return False, tr(f"Suppression impossible ({type(e).__name__}).", f"Cannot delete ({type(e).__name__}).")
    return True, tr(f"Clé supprimée du {nom_coffre()}.", f"Key removed from {nom_coffre()}.")


def tester_cle(cle=None):
    """Teste une clé (ou la clé courante) via un appel gratuit (liste des modèles). Renvoie (ok, message)."""
    if not cle:
        cle, _ = trouver_cle()
    if not format_cle_valide(cle):
        return False, tr("Aucune clé valide à tester (elle doit commencer par sk-ant-).", "No valid key to test (it must start with sk-ant-).")
    try:
        import anthropic
        anthropic.Anthropic(api_key=cle.strip(), max_retries=0, timeout=15).models.list(limit=1)
        return True, tr("Clé acceptée par l'API Anthropic.", "Key accepted by the Anthropic API.")
    except Exception as e:
        import anthropic
        if isinstance(e, anthropic.AuthenticationError):
            return False, tr("Clé refusée par l'API Anthropic.", "Key rejected by the Anthropic API.")
        if isinstance(e, anthropic.PermissionDeniedError):
            return False, tr("Clé reconnue mais sans permission suffisante.", "Key recognised but without sufficient permission.")
        if isinstance(e, (anthropic.APIConnectionError, anthropic.APITimeoutError)):
            return False, tr("Connexion à l'API impossible : vérifie ta connexion Internet.", "Cannot reach the API: check your Internet connection.")
        return False, tr(f"Test impossible : {type(e).__name__}.", f"Test failed: {type(e).__name__}.")


# ---------------------------------------------------------------- console grandMA3

def tester_osc(hote: str, port):
    """Vérifie l'adresse et envoie un message UDP. OSC est à sens unique : la réception n'est PAS confirmée."""
    hote_v, e1 = _valider("osc_hote", hote)
    port_v, e2 = _valider("osc_port", port)
    if e1 or e2:
        return False, e1 or e2
    try:
        socket.getaddrinfo(hote_v, port_v, type=socket.SOCK_DGRAM)
    except OSError:
        return False, tr(f"Adresse introuvable : {hote_v}.", f"Address not found: {hote_v}.")
    try:
        from pythonosc.udp_client import SimpleUDPClient
        import journal
        commande = "Echo 'ma3-ia : test de connexion'"
        SimpleUDPClient(hote_v, port_v).send_message("/cmd", commande)
        with journal.source("Test de connexion"):
            journal.noter(commande, f"{hote_v}:{port_v}")
    except Exception as e:
        return False, tr(f"Envoi impossible : {type(e).__name__} : {e}", f"Cannot send: {type(e).__name__}: {e}")
    return True, tr(f"Message envoyé à {hote_v}:{port_v} (UDP). La console ne répond pas en OSC : "
                    "regarde si « ma3-ia : test de connexion » apparaît dans sa ligne de commande / son historique.",
                    f"Message sent to {hote_v}:{port_v} (UDP). The console does not reply over OSC: "
                    "check that 'ma3-ia : test de connexion' appears in its command line / history.")


def verifier_plugin(bibliotheque: str) -> dict:
    """Vérifie l'environnement : bibliothèque, plugin AI_Index importé, index JSON déjà produit."""
    # Chemin collé depuis l'Explorateur / le Finder : guillemets, espaces, %VARIABLES%, ~.
    bib = str(bibliotheque or "").strip().strip('"').strip()
    bib = os.path.normpath(os.path.expandvars(os.path.expanduser(bib))) if bib else BIBLIOTHEQUE_DEFAUT
    plugin = os.path.join(bib, "datapools", "plugins", PLUGIN_FICHIER)
    index = os.path.join(bib, "ai_index.json")
    res = {"bibliotheque": bib, "bibliotheque_ok": os.path.isdir(bib), "plugin_ok": os.path.isfile(plugin), "plugin_chemin": plugin,
           "index_ok": os.path.isfile(index), "index_age_min": None,
           "lua_source": chemin_plugin_lua()}
    if res["index_ok"]:
        res["index_age_min"] = round((time.time() - os.path.getmtime(index)) / 60)
    return res
