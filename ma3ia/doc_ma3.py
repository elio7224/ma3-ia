"""Consultation du manuel officiel grandMA3 (pages des mots-clés) pour l'outil doc_grandma3.

Les pages sont téléchargées à la demande depuis help.malighting.com, converties en texte,
puis gardées en cache dans %APPDATA%\\ma3-ia\\doc_ma3 (le manuel n'est pas fourni avec le code).
"""
import html
import os
import re
import urllib.request
from html.parser import HTMLParser

from i18n import tr

VERSION_MANUEL = "2.5"
BASE = f"https://help.malighting.com/grandMA3/{VERSION_MANUEL}/HTML/"
PAGE_INDEX = "csk_general_keywords.html"
TAILLE_MAX = 12000

# Pages générales utiles en plus des mots-clés.
PAGES_SPECIALES = {
    "syntaxe": "csk_syntax_rules", "options": "option_keywords",
    "parent": "csk_parent_child", "next": "csk_next_previous_concept",
}
# Mots-clés dont le nom de page ne se devine pas.
ALIAS = {"go+": "goplus", "go": "goplus", "go-": "gominus", "+": "plus", "-": "minus", "*": "asterisk",
         ".": "dot", "/": "slash", "$": "dollarsign", ";": "semicolon", "%": "percent", "=": "equal"}


def dossier_cache() -> str:
    from reglages import dossier_config
    d = os.path.join(dossier_config(), "doc_ma3")
    os.makedirs(d, exist_ok=True)
    return d


def _telecharger(page: str) -> str:
    req = urllib.request.Request(BASE + page + ".html", headers={"User-Agent": "MA3-IA"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode("utf-8", "replace")


class _VersTexte(HTMLParser):
    BLOCS = {"p", "div", "br", "tr", "h1", "h2", "h3", "h4", "li", "pre", "table"}

    def __init__(self):
        super().__init__()
        self.morceaux, self.ignore = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.ignore += 1
        if tag in self.BLOCS:
            self.morceaux.append("\n")
        if tag in ("h1", "h2", "h3", "h4"):
            self.morceaux.append("#" * int(tag[1]) + " ")
        elif tag == "li":
            self.morceaux.append("- ")
        elif tag in ("td", "th"):
            self.morceaux.append(" | ")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.ignore -= 1
        if tag in self.BLOCS:
            self.morceaux.append("\n")

    def handle_data(self, data):
        if not self.ignore:
            self.morceaux.append(data)


def html_vers_texte(page_html: str) -> str:
    """Garde seulement le contenu de l'article du manuel, en texte façon Markdown."""
    debut = page_html.find('<div id="offline-content">')
    if debut < 0:
        debut = max(page_html.find("<article"), 0)
    fin = page_html.find("</article>", debut)
    titre = re.search(r"<title>(.*?)</title>", page_html, re.S)
    p = _VersTexte()
    p.feed(page_html[debut:fin if fin > 0 else None])
    txt = html.unescape("".join(p.morceaux)).replace("\xa0", " ")
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r" *\n *", "\n", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt).strip()
    entete = html.unescape(titre.group(1)).strip() if titre else ""
    return f"# {entete}\n\n{txt}\n"


def _page(nom: str) -> str:
    """Texte d'une page (cache, sinon téléchargement puis mise en cache)."""
    chemin = os.path.join(dossier_cache(), nom + ".md")
    if os.path.exists(chemin):
        with open(chemin, encoding="utf-8") as f:
            return f.read()
    texte = html_vers_texte(_telecharger(nom))
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(texte)
    return texte


def _mots_cles() -> list:
    """Noms des pages mots-clés (ex 'keyword_store'), lus dans la page d'index du manuel."""
    chemin = os.path.join(dossier_cache(), "_liste_mots_cles.txt")
    if os.path.exists(chemin):
        with open(chemin, encoding="utf-8") as f:
            return f.read().split()
    noms = sorted(set(re.findall(r'href="(keyword_[a-z0-9_]+)\.html"', _telecharger(PAGE_INDEX[:-5]))))
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("\n".join(noms))
    return noms


def _simplifier(txt: str) -> str:
    return re.sub(r"[^a-z0-9]", "", txt.lower())


def trouver_page(mot_cle: str, noms: list):
    """Nom de page correspondant à un mot-clé, ou (None, suggestions)."""
    brut = mot_cle.strip().lower()
    if brut in PAGES_SPECIALES:
        return PAGES_SPECIALES[brut], []
    if brut in ALIAS:
        return "keyword_" + ALIAS[brut], []
    cible = _simplifier(brut)
    for n in noms:
        if _simplifier(n[len("keyword_"):]) == cible:
            return n, []
    proches = [n[len("keyword_"):] for n in noms if cible and cible in _simplifier(n)]
    return None, proches[:15]


def _nettoyer(texte: str) -> str:
    """Retire le bruit de mise en page du manuel (cellules vides, fil d'Ariane, boutons)."""
    garde = []
    for ligne in texte.split("\n"):
        l = ligne.strip()
        if l in ("|", "Paste to Command Line", "####") or l.startswith("grandMA3 User Manual »") or l.startswith("Version "):
            continue
        garde.append(ligne.replace("User name[Fixture]>", "> ").replace(">  ", "> "))
    return re.sub(r"\n{3,}", "\n\n", "\n".join(garde)).strip()


def doc_grandma3(mot_cle: str = "") -> str:
    if not mot_cle or not mot_cle.strip():
        return tr("Indique un mot-clé grandMA3 (ex : Store, Assign, Go+, MAtricks) ou 'syntaxe' / 'options'.", "Give a grandMA3 keyword (e.g. Store, Assign, Go+, MAtricks) or 'syntaxe' / 'options'.")
    try:
        page, proches = trouver_page(mot_cle, _mots_cles())
        if page is None:
            aide = tr(" Mots-clés proches : ", " Close keywords: ") + ", ".join(proches) + "." if proches else ""
            return tr(f"Aucune page du manuel pour '{mot_cle}'.", f"No manual page for '{mot_cle}'.") + aide
        texte = _nettoyer(_page(page))
    except OSError as e:
        return tr(f"Erreur : manuel grandMA3 inaccessible (pas d'internet ?) : {e}", f"Error: grandMA3 manual unreachable (no Internet?): {e}")
    if len(texte) > TAILLE_MAX:
        texte = texte[:TAILLE_MAX] + "\n... " + tr("[page coupée : la syntaxe et les exemples principaux sont au-dessus]", "[page cut: the syntax and main examples are above]")
    return tr("(Manuel officiel grandMA3 ", "(Official grandMA3 manual ") + f"{VERSION_MANUEL})\n{texte}"
