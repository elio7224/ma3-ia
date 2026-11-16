"""Outils exposés au modèle : définitions (TOOLS) et fonctions (FUNCS), partagés par app.py et agent.py."""
from doc_ma3 import doc_grandma3
from tools import (
    configure_matricks,
    create_macro,
    generate_fx_grid,
    generate_macros_from_template,
    lire_xml_temp,
    run_command,
)

TOOLS = [
    {
        "name": "doc_grandma3",
        "description": (
            "Consulte la page du manuel officiel grandMA3 pour un mot-clé (syntaxe, options, exemples). "
            "À utiliser quand tu n'es pas sûr d'une commande AVANT de l'envoyer, ou pour expliquer un mot-clé. "
            "Exemples : 'Store', 'Assign', 'Go+', 'MAtricks', 'SetUserVariable'. "
            "'syntaxe' = règles générales, 'options' = liste des options (/Merge, /NoConfirmation…)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"mot_cle": {"type": "string", "description": "Mot-clé grandMA3, ex : Store"}},
            "required": ["mot_cle"]
        }
    },
    {
        "name": "lire_xml_temp",
        "description": (
            "Lit le XML d'un objet exporté (macro, groupe, séquence, preset, layout, shape, matricks), "
            "par NUMÉRO de pool ou par NOM. Formats : 'macros/2002', 'matricks/7', 'presets/4.12', "
            "ou un nom exact de l'index. Si plusieurs objets correspondent, l'outil liste les candidats. "
            "Le XML est rendu en format compact : '[ID 401-412]' regroupe des projecteurs ayant la même valeur, "
            "et les presets dont dépend l'objet sont seulement listés (les lire à part si besoin). "
            "Un objet très long est découpé en parties : lire toi-même les parties suivantes avec 'partie' si nécessaire, sans demander à l'utilisateur."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "nom_objet": {"type": "string", "description": "'section/numéro' (ex : macros/2002) ou nom exact de l'index"},
                "partie": {"type": "integer", "description": "Numéro de la partie à lire (1 par défaut)", "minimum": 1},
            },
            "required": ["nom_objet"]
        }
    },
    {
        "name": "configure_matricks",
        "description": "Crée ou configure un objet MAtricks spécifique (XGroup, XBlock, XWings, Interleave).",
        "input_schema": {
            "type": "object",
            "properties": {
                "number": {"type": "integer"},
                "name": {"type": "string"},
                "xgroup": {"type": "integer"},
                "xblock": {"type": "integer"},
                "xwings": {"type": "integer"},
                "interleave": {"type": "integer"}
            },
            "required": ["number", "name"]
        }
    },
    {
        "name": "create_macro",
        "description": "Crée une macro grandMA3 unitaire (Full Access).",
        "input_schema": {
            "type": "object",
            "properties": {
                "number": {"type": "integer"},
                "name": {"type": "string"},
                "lines": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["number", "name", "lines"]
        }
    },
    {
        "name": "run_command",
        "description": "Envoie N'IMPORTE QUELLE commande grandMA3 directe (Full Access).",
        "input_schema": {
            "type": "object",
            "properties": {"cmd": {"type": "string"}},
            "required": ["cmd"]
        }
    },
    {
        "name": "generate_fx_grid",
        "description": "Génère des macros grandMA3 en masse.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_macro": {"type": "integer"},
                "group_start": {"type": "integer"},
                "group_count": {"type": "integer"},
                "phases": {"type": "array", "items": {"type": "integer"}}
            },
            "required": ["start_macro", "group_start", "group_count", "phases"]
        }
    },
    {
        "name": "generate_macros_from_template",
        "description": (
            "Génère des dizaines ou centaines de macros d'un coup à partir d'un MODÈLE (le code Python fait les boucles, "
            "tu n'écris PAS chaque macro). Variables disponibles dans name_template et line_templates : "
            "{macro} = numéro de la macro courante, {idx} = 0,1,2..., et une variable par boucle (ex {g}, {s}). "
            "Calculs simples autorisés dans les accolades : {macro+1}, {g+25}, {idx*2}. "
            "Les boucles sont imbriquées, la première est la plus externe. "
            "Une boucle est soit {var, start, count, step} (nombres), soit {var, values:[textes]}. "
            "Pas de guillemets doubles dans les modèles (guillemets simples uniquement). "
            "dry_run=true renvoie un aperçu sans rien envoyer à la console."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "start_macro": {"type": "integer", "description": "Numéro de la première macro"},
                "name_template": {"type": "string"},
                "line_templates": {"type": "array", "items": {"type": "string"}},
                "loops": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "var": {"type": "string"},
                            "start": {"type": "integer"},
                            "count": {"type": "integer"},
                            "step": {"type": "integer"},
                            "values": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["var"]
                    }
                },
                "macro_step": {"type": "integer", "description": "Pas entre deux numéros de macro (défaut 1)"},
                "dry_run": {"type": "boolean"},
                "ecraser": {"type": "boolean", "description": "true = autorise à écraser des macros déjà présentes dans le show (refusé sinon). À n'utiliser qu'après accord de l'utilisateur."}
            },
            "required": ["start_macro", "name_template", "line_templates"]
        }
    }
]

FUNCS = {
    "doc_grandma3": doc_grandma3,
    "lire_xml_temp": lire_xml_temp,
    "configure_matricks": configure_matricks,
    "create_macro": create_macro,
    "run_command": run_command,
    "generate_fx_grid": generate_fx_grid,
    "generate_macros_from_template": generate_macros_from_template
}


def textes_de(contenu) -> str:
    """Concatène les blocs texte d'une réponse du modèle."""
    return "".join(b.text for b in contenu if b.type == "text").strip()
