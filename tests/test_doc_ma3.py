"""Outil doc_grandma3 testé sans internet (téléchargement remplacé)."""
import doc_ma3

PAGE = """<html><head><title>Store Keyword</title></head><body>
<div id="offline-content"><h2>Syntax</h2><p>Store [Object] (/Option)</p>
<ul><li>/Merge</li></ul><script>x()</script></div></article></body></html>"""
INDEX = '<a href="keyword_store.html">Store</a> <a href="keyword_goplus.html">Go+</a> <a href="keyword_clear_all.html">ClearAll</a>'


def _hors_ligne(monkeypatch, tmp_path):
    appels = []
    def faux(page):
        appels.append(page)
        return INDEX if page == "csk_general_keywords" else PAGE
    monkeypatch.setattr(doc_ma3, "_telecharger", faux)
    monkeypatch.setattr(doc_ma3, "dossier_cache", lambda: str(tmp_path))
    return appels


def test_page_convertie_et_mise_en_cache(monkeypatch, tmp_path):
    appels = _hors_ligne(monkeypatch, tmp_path)
    r = doc_ma3.doc_grandma3("store")
    assert "Store [Object] (/Option)" in r and "- /Merge" in r and "x()" not in r
    doc_ma3.doc_grandma3("Store")
    assert appels.count("keyword_store") == 1      # 2e appel servi par le cache


def test_noms_speciaux(monkeypatch, tmp_path):
    _hors_ligne(monkeypatch, tmp_path)
    noms = doc_ma3._mots_cles()
    assert doc_ma3.trouver_page("Go+", noms)[0] == "keyword_goplus"
    assert doc_ma3.trouver_page("ClearAll", noms)[0] == "keyword_clear_all"
    assert doc_ma3.trouver_page("syntaxe", noms)[0] == "csk_syntax_rules"
    page, proches = doc_ma3.trouver_page("clear", noms)
    assert page is None and "clear_all" in proches


def test_hors_connexion(monkeypatch, tmp_path):
    def panne(page):
        raise OSError("pas de réseau")
    monkeypatch.setattr(doc_ma3, "_telecharger", panne)
    monkeypatch.setattr(doc_ma3, "dossier_cache", lambda: str(tmp_path))
    assert doc_ma3.doc_grandma3("Store").startswith("Erreur")
