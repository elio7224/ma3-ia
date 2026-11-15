"""Vérifie s'il existe une version plus récente de MA3-IA dans les Releases GitHub.

Un seul appel anonyme à l'API publique de GitHub (aucune donnée envoyée), mis en cache 6 h.
Désactivable dans les Réglages (« verifier_mises_a_jour »). Toute erreur réseau est silencieuse.
"""
import json
import re
import time
import urllib.request

from version import URL, VERSION

API_RELEASES = "https://api.github.com/repos/elio7224/ma3-ia/releases/latest"
DUREE_CACHE_S = 6 * 3600
_cache = {"heure": 0.0, "resultat": None}


def _numeros(version: str) -> tuple:
    """'v1.10.2' -> (1, 10, 2) ; texte illisible -> ()."""
    return tuple(int(n) for n in re.findall(r"\d+", version or "")[:3])


def _derniere_release() -> dict:
    req = urllib.request.Request(API_RELEASES, headers={"User-Agent": "MA3-IA", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.load(r)


def verifier(force: bool = False) -> dict:
    """{actuelle, derniere, nouvelle, url}. 'derniere' vaut None si GitHub est injoignable."""
    if not force and _cache["resultat"] and time.time() - _cache["heure"] < DUREE_CACHE_S:
        return _cache["resultat"]
    res = {"actuelle": VERSION, "derniere": None, "nouvelle": False, "url": URL + "/releases/latest"}
    try:
        rel = _derniere_release()
        tag = str(rel.get("tag_name", ""))
        res["derniere"] = tag.lstrip("v") or None
        res["url"] = rel.get("html_url") or res["url"]
        res["nouvelle"] = bool(_numeros(tag)) and _numeros(tag) > _numeros(VERSION)
    except Exception:
        pass
    _cache.update(heure=time.time(), resultat=res)
    return res
