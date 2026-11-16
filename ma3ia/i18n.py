"""Langue de l'interface (français / anglais) pour les messages renvoyés par le serveur.

Réglage « langue » : "auto" (langue du système), "fr" ou "en". La variable d'environnement MA3IA_LANGUE
force la langue (utile pour les tests). Usage : tr("Clé enregistrée.", "Key saved.").
"""
import functools
import locale
import os
import sys

LANGUES = ("auto", "fr", "en")


def _langue_mac():
    """Première langue préférée de macOS ('fr-FR', 'en-US'…), ou None. Une app lancée depuis le Finder n'a pas de LANG."""
    import subprocess
    try:
        sortie = subprocess.run(["defaults", "read", "-g", "AppleLanguages"], capture_output=True,
                                text=True, timeout=2).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    for ligne in sortie.splitlines():
        code = ligne.strip().strip('(),"').strip()
        if code:
            return code
    return None


@functools.lru_cache(maxsize=1)
def langue_systeme() -> str:
    """'fr' si le système (Windows, macOS ou la locale) est en français, sinon 'en'. Lu une seule fois."""
    if sys.platform == "win32":
        try:
            import ctypes
            return "fr" if (ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF) == 0x0C else "en"   # 0x0C = LANG_FRENCH
        except Exception:
            pass
    if sys.platform == "darwin":
        code = _langue_mac()
        if code:
            return "fr" if code.lower().startswith("fr") else "en"
    code = (locale.getlocale()[0] or os.environ.get("LANG") or "").lower()
    return "fr" if code.startswith("fr") else "en"


def langue() -> str:
    """Langue effective : 'fr' ou 'en'."""
    force = os.environ.get("MA3IA_LANGUE", "").lower()
    if force in ("fr", "en"):
        return force
    try:
        from reglages import charger
        choix = charger().get("langue", "auto")
    except Exception:
        choix = "auto"
    return choix if choix in ("fr", "en") else langue_systeme()


def tr(fr: str, en: str) -> str:
    return en if langue() == "en" else fr
