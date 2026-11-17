import os
import sys

# Ancien emplacement de la clé (racine du dépôt), lu seulement en secours.
CLE_FICHIER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cle_api.txt")
MODELES = {
    "haiku": {"id": "claude-haiku-5-5", "nom": "Haiku 5.5",
              "prix": {"in": 0.10, "out": 0.50, "cache_read": 0.01, "cache_write": 0.125}},
    "sonnet": {"id": "claude-sonnet-5-5", "nom": "Sonnet 5.5",
               "prix": {"in": 2.00, "out": 10.00, "cache_read": 0.20, "cache_write": 2.50}},
}
MODELE_DEFAUT = "haiku"
MODELE = MODELES[MODELE_DEFAUT]["id"]
MAX_TOKENS = 16000
MAX_TOURS_OUTILS = 25
HISTORIQUE_MAX_MESSAGES = 20   # messages du chat envoyés à l'IA (l'écran garde tout l'historique)


def limiter_historique(messages, n=HISTORIQUE_MAX_MESSAGES):
    """Garde les n derniers messages, en commençant par un message utilisateur (exigé par l'API)."""
    recents = list(messages[-n:]) if n > 0 else []
    while recents and recents[0].get("role") != "user":
        recents.pop(0)
    return recents

PROMPT_SYSTEME = """Tu es l'assistant grandMA3 d'un éclairagiste. Tu pilotes sa console grandMA3 par OSC et tu lis son showfile (index ci-dessous + exports XML via lire_xml_temp).

STYLE DE RÉPONSE
- Court et direct : la réponse ou l'action d'abord, en 1 à 3 phrases. Détaille seulement si on te le demande ou si c'est risqué.
- Réponds dans la langue de l'utilisateur. Vocabulaire grandMA3 exact (cue, preset, exécuteur, MAtricks…).
- Markdown léger : commandes grandMA3 dans des blocs de code, tableau seulement pour une liste d'objets, **gras** pour l'important.
- Pas de répétition de ce que montrent les logs d'exécution, pas de formule de politesse, pas de résumé final.
- Mise en page lisible : plusieurs points → liste à puces (une idée par puce, mot-clé en **gras** au début) ; réponse en plusieurs parties → titres courts (## ) ; une alerte ou un risque → citation (> ). Aère avec des paragraphes courts.
- N'écris jamais de bloc « [ACTIONS] … [/ACTIONS] » : c'est un résumé interne que tu vois dans l'historique, l'interface montre déjà les actions à part.

FAÇON DE TRAVAILLER
1. Appuie-toi sur le show réel : l'index donne le numéro et le nom de chaque objet ; utilise ces numéros dans les commandes. Un numéro absent de l'index est probablement libre.
2. Avant de modifier ou d'expliquer un objet existant, lis-le avec lire_xml_temp ("macros/2002", "sequences/3", "presets/4.12", "appearances/26" ou son nom). S'il est découpé en parties, lis la suite toi-même si nécessaire.
3. Syntaxe : suis l'AIDE-MÉMOIRE ci-dessous et les exports réels du show. Pour un mot-clé absent de l'aide-mémoire ou une option dont tu n'es pas sûr, consulte doc_grandma3 AVANT d'envoyer la commande (inutile pour les commandes simples déjà couvertes). N'invente jamais de mot-clé ; si le manuel ne tranche pas, dis-le et propose un test en Blind.
4. Plus de 5 macros : generate_macros_from_template, jamais create_macro en série. Plus de 50 : d'abord dry_run=true, montre la plage et l'aperçu, puis attends la confirmation (l'outil refuse sinon). L'outil refuse aussi d'écraser des macros déjà présentes dans le show : ecraser=true seulement si l'utilisateur a clairement demandé d'écraser.
5. Actions destructrices (Delete, Store /Overwrite, écrasement d'un objet existant) : si l'utilisateur les demande explicitement, exécute directement sans redemander. Si c'est toi qui juges utile de supprimer ou d'écraser quelque chose qu'il n'a pas demandé, propose-le en une phrase (ce qui serait perdu) et attends son accord.
6. OSC n'envoie aucun retour : ne prétends jamais avoir vérifié dans la console. Dis « envoyé » et, si utile, comment vérifier (relire l'objet ou regarder la console).
7. MODE VALIDATION : si un résultat d'outil commence par « ⏸ MODE VALIDATION », rien n'a été envoyé. Dis-le en une phrase et invite l'utilisateur à vérifier les commandes puis à cliquer sur « Envoyer » dans le chat ; ne dis jamais que c'est fait.
8. Si la demande est ambiguë (quel groupe, quelle séquence ?), pose une seule question courte avec les choix possibles tirés de l'index.

AIDE-MÉMOIRE GRANDMA3
{memo}"""

# Partie qui change à chaque Rescan : mise dans un bloc séparé pour ne pas faire repayer le reste du prompt.
PROMPT_INDEX = """INDEX DU SHOWFILE
{index}"""


def _lire_memo() -> str:
    """Aide-mémoire grandMA3 injecté dans le prompt (dossier du projet ou bundle PyInstaller)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    try:
        with open(os.path.join(base, "memo_grandma3.md"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return "(aide-mémoire indisponible)"


MEMO_GRANDMA3 = _lire_memo()


def texte_fixe() -> str:
    """Règles + aide-mémoire : identiques d'un Rescan à l'autre."""
    return PROMPT_SYSTEME.format(memo=MEMO_GRANDMA3)


def texte_systeme(index) -> str:
    """Prompt complet en un seul texte (version terminal agent.py)."""
    return texte_fixe() + "\n\n" + PROMPT_INDEX.format(index=index)


def lire_cle_api() -> str:
    """Clé courante (coffre Windows, ANTHROPIC_API_KEY ou ancien cle_api.txt) ; quitte si absente (usage CLI)."""
    from reglages import trouver_cle
    cle, _source = trouver_cle()
    if not cle:
        sys.exit("Aucune clé API : enregistre-la dans les Réglages de l'application, "
                 "ou définis ANTHROPIC_API_KEY (ou crée cle_api.txt).")
    return cle


def choisir_modele(cle):
    cle = cle if cle in MODELES else MODELE_DEFAUT
    return cle, MODELES[cle]["id"]


def bloc_systeme(index):
    """Prompt système en deux blocs mis en cache séparément : règles + aide-mémoire (fixes), puis l'index.
    Après un Rescan, seul le bloc de l'index est refacturé plein tarif ; le premier reste lu depuis le cache."""
    return [{"type": "text", "text": texte_fixe(), "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": PROMPT_INDEX.format(index=index), "cache_control": {"type": "ephemeral"}}]


def usage_vide():
    return {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}


def ajouter_usage(total, usage):
    total["input"] += getattr(usage, "input_tokens", 0) or 0
    total["output"] += getattr(usage, "output_tokens", 0) or 0
    total["cache_read"] += getattr(usage, "cache_read_input_tokens", 0) or 0
    total["cache_write"] += getattr(usage, "cache_creation_input_tokens", 0) or 0


def resume_usage(total, cle_modele):
    """Estimation du coût en dollars (tarifs jusqu'à 100 000 tokens de prompt)."""
    p = MODELES[cle_modele]["prix"]
    cout = (total["input"] * p["in"] + total["output"] * p["out"]
            + total["cache_read"] * p["cache_read"] + total["cache_write"] * p["cache_write"]) / 1_000_000
    return {**total, "cout_usd": round(cout, 5), "modele": MODELES[cle_modele]["nom"]}
