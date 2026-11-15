import json
import os

import anthropic

import tools
from config import (MAX_TOKENS, MAX_TOURS_OUTILS, MODELES, texte_systeme, ajouter_usage, choisir_modele,
                    lire_cle_api, resume_usage, usage_vide)
from outils import FUNCS, TOOLS, textes_de

client = anthropic.Anthropic(api_key=lire_cle_api())


def banque_exemples() -> str:
    dossier = "exemples"
    if not os.path.isdir(dossier):
        return "Aucun exemple."
    blocs = []
    for nom in sorted(os.listdir(dossier)):
        chemin = os.path.join(dossier, nom)
        if os.path.isfile(chemin):
            try:
                with open(chemin, encoding="utf-8") as f:
                    blocs.append(f"--- EXEMPLE ({nom}) ---\n{f.read()}")
            except (OSError, UnicodeDecodeError) as e:
                print(f"Exemple ignoré ({nom}) : {e}")
    return "\n\n".join(blocs) or "Aucun exemple."


def traiter(messages, system, modele_id, usage):
    """Boucle outils. Retourne (texte, ok)."""
    for _ in range(MAX_TOURS_OUTILS):
        try:
            r = client.messages.create(model=modele_id, max_tokens=MAX_TOKENS, system=system,
                                       tools=TOOLS, messages=messages)
        except anthropic.AuthenticationError:
            return "Clé API refusée : vérifie cle_api.txt.", False
        except anthropic.RateLimitError:
            return "Limite de débit atteinte : attends une minute.", False
        except anthropic.APIError as e:
            return f"Erreur API : {e}", False

        ajouter_usage(usage, r.usage)

        if r.stop_reason == "max_tokens":
            return "Réponse coupée (trop longue), rien n'a été exécuté.", False

        messages.append({"role": "assistant", "content": r.content})
        appels = [b for b in r.content if b.type == "tool_use"]
        if not appels:
            return textes_de(r.content) or "✅ Terminé.", True

        resultats = []
        for b in appels:
            print(f"\n⚡ {b.name}({json.dumps(b.input, ensure_ascii=False)})")
            try:
                res, erreur = FUNCS[b.name](**b.input), False
            except Exception as e:
                res, erreur = f"Erreur d'exécution : {type(e).__name__} : {e}", True
            print(f"   ➔ {res}")
            bloc = {"type": "tool_result", "tool_use_id": b.id, "content": str(res)}
            if erreur:
                bloc["is_error"] = True
            resultats.append(bloc)
        messages.append({"role": "user", "content": resultats})
    return f"Limite de {MAX_TOURS_OUTILS} tours d'outils atteinte.", False


def main():
    print("🧹 Export et lecture de l'index...")
    tools.preparer_et_exporter_show()
    texte_prompt = texte_systeme(tools.charger_contexte_temp()) + "\n\nEXEMPLES DE RÉFÉRENCE :\n" + banque_exemples()
    system = [{"type": "text", "text": texte_prompt, "cache_control": {"type": "ephemeral"}}]
    cle_modele, modele_id = choisir_modele(input("Modèle (haiku / sonnet) [haiku] : ").strip().lower())
    print(f"Modèle : {MODELES[cle_modele]['nom']}")

    messages = []
    print("🚀 Agent grandMA3 prêt (ligne vide pour quitter).")
    while True:
        demande = input("\nQue veux-tu faire ? ").strip()
        if not demande:
            break
        debut = len(messages)
        messages.append({"role": "user", "content": demande})
        usage = usage_vide()
        texte, ok = traiter(messages, system, modele_id, usage)
        print("\n" + texte)
        bilan = resume_usage(usage, cle_modele)
        entree = bilan["input"] + bilan["cache_read"] + bilan["cache_write"]
        print(f"\n💰 ≈ {bilan['cout_usd']:.4f} $ ({entree} tokens en entrée dont {bilan['cache_read']} en cache, {bilan['output']} en sortie)")
        if not ok:
            del messages[debut:]


if __name__ == "__main__":
    main()
