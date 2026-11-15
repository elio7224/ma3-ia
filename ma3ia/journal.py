"""Journal des commandes envoyées à la console (une ligne JSON par commande, conservé entre deux lancements).

Chaque commande OSC passe par MA3.send, qui appelle noter(). La source (« IA · create_macro », « Rescan »…)
est fixée par le code appelant avec `with source("...")` ; par défaut : « App ».
"""
import json
import os
import threading
from contextlib import contextmanager
from datetime import datetime

MAX_LIGNES = 5000        # au-delà, les plus anciennes lignes sont supprimées
_verrou = threading.Lock()
_local = threading.local()


def fichier_journal() -> str:
    from reglages import dossier_config
    return os.path.join(dossier_config(), "journal_actions.jsonl")


@contextmanager
def source(nom: str):
    """Attribue les commandes envoyées dans ce bloc à `nom` (ex : « IA · create_macro »)."""
    precedente = getattr(_local, "source", None)
    _local.source = nom
    try:
        yield
    finally:
        _local.source = precedente


def noter(commande: str, cible: str = ""):
    """Ajoute une commande au journal. Ne lève jamais d'exception (le journal ne doit pas bloquer l'envoi)."""
    entree = {"heure": datetime.now().isoformat(timespec="seconds"),
              "source": getattr(_local, "source", None) or "App",
              "commande": commande, "cible": cible}
    try:
        chemin = fichier_journal()
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
        with _verrou:
            with open(chemin, "a", encoding="utf-8") as f:
                f.write(json.dumps(entree, ensure_ascii=False) + "\n")
            _elaguer(chemin)
    except Exception:
        pass


def _elaguer(chemin: str):
    if os.path.getsize(chemin) < MAX_LIGNES * 120:      # vérification rapide avant de relire le fichier
        return
    with open(chemin, encoding="utf-8") as f:
        lignes = f.readlines()
    if len(lignes) > MAX_LIGNES:
        with open(chemin, "w", encoding="utf-8") as f:
            f.writelines(lignes[-MAX_LIGNES:])


def lire(limite: int = 500) -> list:
    """Dernières entrées, la plus récente en premier."""
    chemin = fichier_journal()
    if not os.path.exists(chemin):
        return []
    with _verrou, open(chemin, encoding="utf-8") as f:
        lignes = f.readlines()
    entrees = []
    for ligne in reversed(lignes[-max(1, limite):]):
        try:
            entrees.append(json.loads(ligne))
        except ValueError:
            continue
    return entrees


def effacer():
    with _verrou:
        try:
            os.remove(fichier_journal())
        except FileNotFoundError:
            pass
