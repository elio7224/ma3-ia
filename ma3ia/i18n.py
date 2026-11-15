"""Langue de l'interface (français / anglais) pour les messages renvoyés par le serveur.

Réglage « langue » : "auto" (langue de Windows), "fr" ou "en". La variable d'environnement MA3IA_LANGUE
force la langue (utile pour les tests). Usage : tr("Clé enregistrée.", "Key saved.").
"""
import locale
import os

LANGUES = ("auto", "fr", "en")


def langue_systeme() -> str:
    """'fr' si Windows (ou la locale) est en français, sinon 'en'."""
    try:
        import ctypes
        if (ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF) == 0x0C:   # 0x0C = LANG_FRENCH
            return "fr"
        return "en"
    except Exception:
        pass
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
