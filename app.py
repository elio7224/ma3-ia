import os
import sys
import threading

# Les messages console contiennent des emojis : sans ça, un print() plante sous Windows (cp1252)
# et l'endpoint renvoie « Internal Server Error » au lieu de JSON (ex. Rescan : « Unexpected token »).
for _flux in (sys.stdout, sys.stderr):
    if _flux is not None and hasattr(_flux, "reconfigure"):
        _flux.reconfigure(encoding="utf-8", errors="replace")

import anthropic
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import FileResponse
import tools
from tools import preparer_et_exporter_show, charger_contexte_temp
from outils import TOOLS, FUNCS
import reglages
import journal
import i18n
from i18n import tr
from config import (MAX_TOKENS, ajouter_usage, limiter_historique, bloc_systeme, choisir_modele, resume_usage, usage_vide)

HISTORIQUE_FICHIER = reglages.chemin_historique()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(127\.0\.0\.1|localhost)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INDEX_SHOW = ""
_client = None
_client_cle = None


def appliquer_reglages_courants():
    """Pousse les réglages (OSC, dossier bibliothèque) vers les outils."""
    r = reglages.charger()
    tools.appliquer_reglages(r["osc_hote"], r["osc_port"], r["dossier_bibliotheque"])
    return r


def obtenir_client():
    """Client Anthropic construit à la demande avec la clé courante ; None si aucune clé."""
    global _client, _client_cle
    cle, _source = reglages.trouver_cle()
    if not cle:
        return None
    if cle != _client_cle:
        _client, _client_cle = anthropic.Anthropic(api_key=cle), cle
    return _client


def _scan_initial():
    global INDEX_SHOW
    print("🧹 Nettoyage et exportation initiales...")
    try:
        with journal.source("Scan au démarrage"):
            preparer_et_exporter_show()
        INDEX_SHOW = charger_contexte_temp()
        print("✅ Contexte initial chargé.")
    except Exception as e:
        print(f"⚠️ Scan initial impossible : {type(e).__name__}")


appliquer_reglages_courants()


@app.on_event("startup")
def demarrage():
    # En arrière-plan : le scan attend la console (jusqu'à ~15 s) et ne doit pas bloquer l'interface.
    threading.Thread(target=_scan_initial, daemon=True).start()


def charger_memoire_disque():
    if os.path.exists(HISTORIQUE_FICHIER):
        try:
            with open(HISTORIQUE_FICHIER, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur chargement mémoire disque: {e}")
    return []


def sauvegarder_memoire_disque(messages):
    try:
        with open(HISTORIQUE_FICHIER, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erreur sauvegarde mémoire disque: {e}")


def conserver_memoire_texte(messages_raw):
    messages_propres = []
    for m in messages_raw:
        role = m.get("role")
        content = m.get("content")
        if role == "user" and isinstance(content, str) and content.strip():
            messages_propres.append({"role": "user", "content": content})
        elif role == "assistant" and isinstance(content, str) and content.strip():
            messages_propres.append({"role": "assistant", "content": content})
        elif role == "assistant" and isinstance(content, list):
            textes = [bloc["text"] for bloc in content if isinstance(bloc, dict) and bloc.get("type") == "text"]
            if textes:
                texte_combine = "\n".join(textes).strip()
                if texte_combine:
                    messages_propres.append({"role": "assistant", "content": texte_combine})
    return messages_propres


@app.get("/")
def read_index():
    page = os.path.join(reglages.dossier_ressources(), "index.html")
    if os.path.exists(page):
        return FileResponse(page)
    else:
        raise HTTPException(status_code=404, detail="index.html introuvable.")


class ChatPayload(BaseModel):
    messages: list
    modele: str = "haiku"


@app.get("/api/history")
def get_history():
    return {"messages": charger_memoire_disque()}


@app.delete("/api/history")
def effacer_historique():
    reglages.effacer_historique()
    return {"status": "success"}


def compter_index():
    return {section: len(objets) for section, objets in tools.INDEX_OBJETS.items()}


@app.get("/api/status")
def status():
    from config import MODELES
    return {"counts": compter_index(), "modeles": {k: v["nom"] for k, v in MODELES.items()},
            "modele_defaut": reglages.charger()["modele_defaut"], "cle": reglages.etat_cle()["presente"],
            "session": etat_session(), "langue": i18n.langue()}


# ---------------------------------------------------------------- garde-fou de coût (session = depuis le lancement)

COUT_SESSION = {"usd": 0.0}
SEUIL_ALERTE = 0.8


def etat_session():
    plafond = reglages.charger()["plafond_session_usd"]
    cout = round(COUT_SESSION["usd"], 5)
    return {"cout_usd": cout, "plafond_usd": plafond,
            "alerte": plafond > 0 and cout >= SEUIL_ALERTE * plafond,
            "atteint": plafond > 0 and cout >= plafond}


@app.post("/api/session/reinitialiser")
def reinitialiser_session():
    COUT_SESSION["usd"] = 0.0
    return etat_session()


# ---------------------------------------------------------------- journal des commandes envoyées à la console

@app.get("/api/journal")
def lire_journal(limite: int = 500):
    return {"entrees": journal.lire(min(max(limite, 1), 5000)), "fichier": journal.fichier_journal()}


@app.delete("/api/journal")
def effacer_journal():
    journal.effacer()
    return {"status": "success"}


# ---------------------------------------------------------------- réglages (jamais de clé en clair dans les réponses)

class ReglagesPayload(BaseModel):
    reglages: dict


class ClePayload(BaseModel):
    cle: str = ""


class OscPayload(BaseModel):
    hote: str
    port: int | str


@app.get("/api/reglages")
def lire_reglages():
    from config import MODELES
    r = reglages.charger()
    return {"reglages": r, "cle": reglages.etat_cle(), "modeles": {k: v["nom"] for k, v in MODELES.items()},
            "langue": i18n.langue(),
            "plugin": reglages.verifier_plugin(r["dossier_bibliotheque"]),
            "fichier": reglages.fichier_reglages()}


@app.post("/api/reglages")
def ecrire_reglages(payload: ReglagesPayload):
    r, erreurs = reglages.enregistrer(payload.reglages)
    if not erreurs:
        appliquer_reglages_courants()
    return {"ok": not erreurs, "erreurs": erreurs, "reglages": r}


@app.post("/api/reglages/cle")
def enregistrer_cle(payload: ClePayload):
    ok, msg = reglages.enregistrer_cle(payload.cle)
    return {"ok": ok, "message": msg, "cle": reglages.etat_cle()}


@app.delete("/api/reglages/cle")
def supprimer_cle():
    ok, msg = reglages.supprimer_cle()
    return {"ok": ok, "message": msg, "cle": reglages.etat_cle()}


@app.post("/api/reglages/tester-cle")
def tester_cle(payload: ClePayload):
    ok, msg = reglages.tester_cle(payload.cle or None)
    return {"ok": ok, "message": msg}


@app.post("/api/reglages/tester-osc")
def tester_osc(payload: OscPayload):
    ok, msg = reglages.tester_osc(payload.hote, payload.port)
    return {"ok": ok, "message": msg}


@app.post("/api/reglages/plugin")
def verifier_plugin(payload: ReglagesPayload):
    chemin = payload.reglages.get("dossier_bibliotheque") or reglages.charger()["dossier_bibliotheque"]
    return reglages.verifier_plugin(chemin)


@app.post("/api/sync")
def sync_show():
    global INDEX_SHOW
    try:
        with journal.source("Rescan"):
            msg = preparer_et_exporter_show()
        INDEX_SHOW = charger_contexte_temp()
    except Exception as e:
        return {"status": "error", "message": tr(f"Rescan impossible : {type(e).__name__} : {e}", f"Rescan failed: {type(e).__name__}: {e}"), "counts": compter_index()}
    counts = compter_index()
    return {"status": "success" if any(counts.values()) else "warning", "message": msg, "counts": counts}


@app.post("/api/chat")
def chat(payload: ChatPayload):
    sauvegarder_memoire_disque(payload.messages)
    messages_nettoyes = limiter_historique(conserver_memoire_texte(payload.messages))
    cle_modele, modele_id = choisir_modele(payload.modele)
    max_tours = reglages.charger()["max_tours_outils"]
    usage = usage_vide()
    logs, actions = [], []

    def reponse(texte, avec_historique=True):
        msgs = payload.messages + [{"role": "assistant", "content": texte}] if avec_historique else payload.messages
        if avec_historique:
            sauvegarder_memoire_disque(msgs)
        return {"response": texte, "logs": logs, "actions": actions, "messages": msgs,
                "usage": resume_usage(usage, cle_modele), "session": etat_session()}

    if not messages_nettoyes:
        return reponse(tr("⚠️ Message vide ou invalide.", "⚠️ Empty or invalid message."), avec_historique=False)

    client = obtenir_client()
    if client is None:
        return reponse(tr("⚠️ Aucune clé API configurée. Ouvre **⚙ Réglages** pour l'enregistrer.", "⚠️ No API key configured. Open **⚙ Settings** to add it."), avec_historique=False)

    if etat_session()["atteint"]:
        s = etat_session()
        return reponse(tr(f"⛔ **Plafond de dépense atteint** ({s['cout_usd']:.2f} $ sur {s['plafond_usd']:.2f} $ pour cette session). "
                          "Remets le compteur à zéro ou relève le plafond dans **⚙ Réglages**.",
                          f"⛔ **Spending limit reached** ({s['cout_usd']:.2f} $ of {s['plafond_usd']:.2f} $ for this session). "
                          "Reset the counter or raise the limit in **⚙ Settings**."), avec_historique=False)

    system = bloc_systeme(INDEX_SHOW)
    historique_ia = messages_nettoyes.copy()
    cout_compte = 0.0

    for _tour in range(max_tours):
        try:
            r = client.messages.create(model=modele_id, max_tokens=MAX_TOKENS, system=system,
                                       tools=TOOLS, messages=historique_ia)
        except anthropic.AuthenticationError:
            return reponse(tr("⚠️ Clé API refusée. Vérifie-la dans ⚙ Réglages.", "⚠️ API key rejected. Check it in ⚙ Settings."), avec_historique=False)
        except anthropic.RateLimitError:
            return reponse(tr("⚠️ Limite de débit atteinte. Attends une minute.", "⚠️ Rate limit reached. Wait a minute."), avec_historique=False)
        except Exception as e:
            return reponse(tr(f"⚠️ Erreur lors de l'appel API : {type(e).__name__} : {e}", f"⚠️ API call error: {type(e).__name__}: {e}"), avec_historique=False)

        ajouter_usage(usage, r.usage)
        cout_requete = resume_usage(usage, cle_modele)["cout_usd"]
        COUT_SESSION["usd"] += cout_requete - cout_compte
        cout_compte = cout_requete

        if r.stop_reason == "max_tokens":
            logs.append(tr("⚠️ Réponse coupée (max_tokens atteint).", "⚠️ Response cut off (max_tokens reached)."))
            texte = "".join(b.text for b in r.content if b.type == "text").strip()
            return reponse((texte + "\n\n" if texte else "") + tr("⚠️ Réponse coupée car trop longue.", "⚠️ Response cut off because it was too long."))

        historique_ia.append({"role": "assistant", "content": r.content})
        appels = [b for b in r.content if b.type == "tool_use"]

        if not appels:
            texte = "".join(b.text for b in r.content if b.type == "text").strip()
            return reponse(texte or "✅ Terminé.")

        if etat_session()["atteint"]:
            logs.append(tr("⛔ Plafond de dépense atteint : actions suivantes annulées.", "⛔ Spending limit reached: remaining actions cancelled."))
            return reponse(tr("⛔ **Plafond de dépense atteint pendant la demande** : j'ai arrêté avant d'envoyer les actions suivantes. "
                              "Remets le compteur à zéro ou relève le plafond dans **⚙ Réglages**, puis redemande.",
                              "⛔ **Spending limit reached during the request**: I stopped before sending the remaining actions. "
                              "Reset the counter or raise the limit in **⚙ Settings**, then ask again."))

        resultats = []
        for b in appels:
            log_entry = f"⚡ Exécution : {b.name}({json.dumps(b.input, ensure_ascii=False)})"
            try:
                with journal.source(f"IA · {b.name}"):
                    res, erreur = FUNCS[b.name](**b.input), False
            except Exception as e:
                res, erreur = f"Erreur d'exécution de l'outil : {type(e).__name__} : {e}", True
            logs.append(log_entry + f" ➔ {res}")
            actions.append({"name": b.name, "input": b.input, "result": str(res), "error": erreur})
            bloc = {"type": "tool_result", "tool_use_id": b.id, "content": str(res)}
            if erreur:
                bloc["is_error"] = True
            resultats.append(bloc)

        historique_ia.append({"role": "user", "content": resultats})

    return reponse(tr(f"⚠️ J'ai atteint la limite de {max_tours} tours d'outils pour une demande.", f"⚠️ I reached the limit of {max_tours} tool rounds for one request."))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)