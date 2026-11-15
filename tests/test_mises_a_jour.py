"""Alerte de nouvelle version (GitHub simulé, aucun appel réseau)."""
import mises_a_jour


def _github(monkeypatch, tag=None, erreur=False):
    def faux():
        if erreur:
            raise OSError("pas de réseau")
        return {"tag_name": tag, "html_url": f"https://github.com/elio7224/ma3-ia/releases/tag/{tag}"}
    monkeypatch.setattr(mises_a_jour, "_derniere_release", faux)
    mises_a_jour._cache.update(heure=0.0, resultat=None)


def test_comparaison_de_versions():
    assert mises_a_jour._numeros("v1.10.0") > mises_a_jour._numeros("1.9.3")
    assert mises_a_jour._numeros("n'importe quoi") == ()


def test_nouvelle_version(monkeypatch):
    monkeypatch.setattr(mises_a_jour, "VERSION", "1.2.0")
    _github(monkeypatch, "v1.3.0")
    r = mises_a_jour.verifier()
    assert r["nouvelle"] and r["derniere"] == "1.3.0" and r["url"].endswith("v1.3.0")


def test_deja_a_jour_et_hors_ligne(monkeypatch):
    monkeypatch.setattr(mises_a_jour, "VERSION", "1.3.0")
    _github(monkeypatch, "v1.3.0")
    assert not mises_a_jour.verifier()["nouvelle"]
    _github(monkeypatch, erreur=True)
    r = mises_a_jour.verifier()
    assert not r["nouvelle"] and r["derniere"] is None
