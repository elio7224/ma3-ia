"""Tests en français quelle que soit la langue de Windows (les tests de traduction forcent eux-mêmes l'anglais)."""
import os
import sys

import pytest

# Le code est dans ma3ia/ et s'importe par nom de module (import tools, import reglages…).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ma3ia"))


@pytest.fixture(autouse=True)
def langue_francaise(monkeypatch):
    monkeypatch.setenv("MA3IA_LANGUE", "fr")


@pytest.fixture(autouse=True)
def bibliotheque_factice(tmp_path, monkeypatch):
    """Les XML de macros sont écrits dans un dossier temporaire, jamais dans la vraie gma3_library."""
    import tools
    from reglages import dossiers_temp
    monkeypatch.setattr(tools, "DOSSIERS_TEMP_MA3", dossiers_temp(str(tmp_path / "bibliotheque_factice")))
    for d in tools.DOSSIERS_TEMP_MA3:
        os.makedirs(d, exist_ok=True)
