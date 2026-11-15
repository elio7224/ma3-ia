"""Tests en français quelle que soit la langue de Windows (les tests de traduction forcent eux-mêmes l'anglais)."""
import pytest


@pytest.fixture(autouse=True)
def langue_francaise(monkeypatch):
    monkeypatch.setenv("MA3IA_LANGUE", "fr")
