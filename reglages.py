"""Couche de réglages de l'application : réglages non secrets (JSON dans %APPDATA%) + clé API (coffre Windows).

- Réglages : %APPDATA%\\ma3-ia\\settings.json (dossier modifiable avec la variable MA3IA_CONFIG_DIR).
- Clé API : Windows Credential Manager via `keyring` ; repli sur ANTHROPIC_API_KEY, puis sur l'ancien cle_api.txt.
- La clé n'est JAMAIS écrite dans settings.json, ni affichée en clair, ni journalisée.
Les fonctions renvoient des dictionnaires / chaînes et ne lèvent pas d'exception vers l'appelant.
"""
import json
import os
import socket
import sys
import time

from config import CLE_FICHIER, MODELE_DEFAUT, MODELES, MAX_TOURS_OUTILS

SERVICE_COFFRE = "ma3-ia"
UTILISATEUR_COFFRE = "anthropic_api_key"
FICHIER_CLE_LEGACY = CLE_FICHIER
BIBLIOTHEQUE_DEFAUT = r"C:\ProgramData\MALightingTechnology\gma3_library"
PLUGIN_FICHIER = "ai_index.xml"   # nom du plugin une fois importé dans la console (datapools/plugins)

DEFAUTS = {
    "modele_defaut": MODELE_DEFAUT,
    "osc_hote": "127.0.0.1",
    "osc_port": 8000,
    "dossier_bibliotheque": BIBLIOTHEQUE_DEFAUT,
    "theme": "sombre",
    "max_tours_outils": MAX_TOURS_OUTILS,
    "premier_lancement_fait": False,
}
THEMES = ("sombre", "clair")


# ---------------------------------------------------------------- chemins

def dossier_config() -> str:
    base = os.environ.get("MA3IA_CONFIG_DIR")
    if not base:
        base = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "ma3-ia")
    return base


def fichier_reglages() -> str:
    return os.path.join(dossier_config(), "settings.json")


def dossier_ressources() -> str:
    """Dossier contenant index.html et ai_index.lua (dossier du projet, ou bundle PyInstaller)."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------- réglages non secrets

def _valider(cle: str, valeur):
    """Renvoie (valeur_nettoyée, None) ou (None, message_d_erreur)."""
    if cle == "modele_defaut":
        return (valeur, None) if valeur in MODELES else (None, f"Modèle inconnu : {valeur!r}.")
    if cle == "osc_hote":
        v = str(valeur).strip()
        return (v, None) if v and " " not in v and len(v) <= 253 else (None, "Adresse IP / nom d'hôte invalide.")
    if cle == "osc_port":
        try:
            p = int(valeur)
        except (TypeError, ValueError):
            return None, "Le port doit être un nombre."
        return (p, None) if 1 <= p <= 65535 else (None, "Le port doit être entre 1 et 65535.")
    if cle == "dossier_bibliotheque":
        v = str(valeur).strip().strip('"')
        return (v, None) if v else (None, "Chemin vide.")
    if cle == "theme":
        return (valeur, None) if valeur in THEMES else (None, f"Thème inconnu : {valeur!r}.")
    if cle == "max_tours_outils":
        try:
            n = int(valeur)
        except (TypeError, ValueError):
            return None, "Le nombre de tours doit être un entier."
        return (n, None) if 1 <= n <= 100 else (None, "Le nombre de tours doit être entre 1 et 100.")
    if cle == "premier_lancement_fait":
        return bool(valeur), None
    return None, f"Réglage inconnu : {cle}."


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
        return courant, {"_fichier": f"Écriture impossible : {e}"}
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
        return "Historique effacé."
    except OSError as e:
        return f"Erreur : {e}"


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
    """Renvoie (ok, message). Stocke dans le coffre Windows."""
    if not format_cle_valide(cle):
        return False, "Clé invalide : elle doit commencer par sk-ant-."
    try:
        _coffre_ecrire(cle.strip())
    except Exception as e:
        return False, f"Coffre indisponible ({type(e).__name__}). Utilise la variable ANTHROPIC_API_KEY."
    return True, "Clé enregistrée dans le coffre Windows."


def supprimer_cle():
    try:
        _coffre_supprimer()
    except Exception as e:
        return False, f"Suppression impossible ({type(e).__name__})."
    return True, "Clé supprimée du coffre Windows."


def tester_cle(cle=None):
    """Teste une clé (ou la clé courante) via un appel gratuit (liste des modèles). Renvoie (ok, message)."""
    if not cle:
        cle, _ = trouver_cle()
    if not format_cle_valide(cle):
        return False, "Aucune clé valide à tester (elle doit commencer par sk-ant-)."
    try:
        import anthropic
        anthropic.Anthropic(api_key=cle.strip(), max_retries=0, timeout=15).models.list(limit=1)
        return True, "Clé acceptée par l'API Anthropic."
    except Exception as e:
        import anthropic
        if isinstance(e, anthropic.AuthenticationError):
            return False, "Clé refusée par l'API Anthropic."
        if isinstance(e, anthropic.PermissionDeniedError):
            return False, "Clé reconnue mais sans permission suffisante."
        if isinstance(e, (anthropic.APIConnectionError, anthropic.APITimeoutError)):
            return False, "Connexion à l'API impossible : vérifie ta connexion Internet."
        return False, f"Test impossible : {type(e).__name__}."


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
        return False, f"Adresse introuvable : {hote_v}."
    try:
        from pythonosc.udp_client import SimpleUDPClient
        SimpleUDPClient(hote_v, port_v).send_message("/cmd", "Echo 'ma3-ia : test de connexion'")
    except Exception as e:
        return False, f"Envoi impossible : {type(e).__name__} : {e}"
    return True, (f"Message envoyé à {hote_v}:{port_v} (UDP). La console ne répond pas en OSC : "
                  "regarde si « ma3-ia : test de connexion » apparaît dans sa ligne de commande / son historique.")


def verifier_plugin(bibliotheque: str) -> dict:
    """Vérifie l'environnement : bibliothèque, plugin AI_Index importé, index JSON déjà produit."""
    # Chemin collé depuis l'Explorateur (« Copier en tant que chemin d'accès ») : guillemets, espaces, %VARIABLES%.
    bib = str(bibliotheque or "").strip().strip('"').strip()
    bib = os.path.normpath(os.path.expandvars(os.path.expanduser(bib))) if bib else BIBLIOTHEQUE_DEFAUT
    plugin = os.path.join(bib, "datapools", "plugins", PLUGIN_FICHIER)
    index = os.path.join(bib, "ai_index.json")
    res = {"bibliotheque": bib, "bibliotheque_ok": os.path.isdir(bib), "plugin_ok": os.path.isfile(plugin), "plugin_chemin": plugin,
           "index_ok": os.path.isfile(index), "index_age_min": None,
           "lua_source": os.path.join(dossier_ressources(), "ai_index.lua")}
    if res["index_ok"]:
        res["index_age_min"] = round((time.time() - os.path.getmtime(index)) / 60)
    return res
