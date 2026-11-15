"""Tests en français quelle que soit la langue de Windows (les tests de traduction forcent eux-mêmes l'anglais)."""
import os
import sys

import pytest

# Le code est dans ma3ia/ et s'importe par nom de module (import tools, import reglages…).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ma3ia"))


@pytest.fixture(autouse=True)
def langue_francaise(monkeypatch):
    monkeypatch.setenv("MA3IA_LANGUE", "fr")
