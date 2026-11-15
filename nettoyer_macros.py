import json
import os
import re
import time
from ma3 import MA3

# Dossier par défaut de grandMA3
BIBLIOTHEQUE = r"C:\ProgramData\MALightingTechnology\gma3_library"
FICHIER_INDEX = os.path.join(BIBLIOTHEQUE, "ai_index.json")

ma3 = MA3()

def exporter_macro(numero: int) -> str:
    """Exporte une macro spécifique dans Temp et retourne le chemin du fichier XML."""
    dossier_temp = os.path.join(BIBLIOTHEQUE, "datapools", "macros", "Temp")
    os.makedirs(dossier_temp, exist_ok=True)
    chemin = os.path.join(dossier_temp, f"{numero}.xml")
    
    if os.path.exists(chemin):
        try:
            os.remove(chemin)
        except OSError:
            pass

    ma3.send(f'Export Macro {numero} "{numero}" /Path "Temp"')

    # Attente de la création du fichier
    fin = time.time() + 3.0
    taille_prec = -1
    while time.time() < fin:
        if os.path.exists(chemin):
            taille = os.path.getsize(chemin)
            if taille > 0 and taille == taille_prec:
                return chemin
            taille_prec = taille
        time.sleep(0.1)
    return None


def reecrire_macro_propre(numero: int, nom: str, lignes_valides: list):
    """Supprime l'ancienne macro et la réécrit proprement sans lignes vides."""
    cmds = [
        f'Delete Macro {numero} /noconfirm',
        f'Store Macro {numero}',
        f'ChangeDestination Macro {numero}'
    ]
    
    for i, line in enumerate(lignes_valides, start=1):
        if i > 1:
            cmds.append("Insert")
        cmds.append(f'Set {i} Property "Command" "{line}"')
        
    cmds.append("ChangeDestination Root")
    cmds.append(f'Label Macro {numero} "{nom}"')

    for cmd in cmds:
        ma3.send(cmd)


def nettoyer_toutes_les_macros(start_range: int = None, end_range: int = None):
    """Parcourt l'index JSON et nettoie les macros concernées."""
    if not os.path.exists(FICHIER_INDEX):
        print(f"❌ Fichier d'index introuvable ({FICHIER_INDEX}). Lance le plugin AI_Index dans MA3 d'abord.")
        return

    try:
        with open(FICHIER_INDEX, encoding="utf-8-sig", errors="replace") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Impossible de lire {FICHIER_INDEX} : {e}")
        return

    # Extraire le pool des macros depuis le JSON
    macros_pool = []
    for pool in data.get("pools", []):
        if "macro" in str(pool.get("pool", "")).lower():
            macros_pool = pool.get("items", [])
            break

    if not macros_pool:
        print("⚠️ Aucune macro trouvée dans l'index JSON.")
        return

    print(f"🔍 {len(macros_pool)} macros trouvées dans l'index.")
    compteur = 0

    for item in macros_pool:
        no = item.get("no")
        nom = item.get("name", "Macro")
        
        if no is None:
            continue
            
        num = int(no)

        # Filtrer par plage si spécifiée
        if start_range is not None and num < start_range:
            continue
        if end_range is not None and num > end_range:
            continue

        # 1. Exporter le XML
        chemin_xml = exporter_macro(num)
        if not chemin_xml:
            continue

        # 2. Lire les lignes de commande
        try:
            with open(chemin_xml, encoding="utf-8", errors="ignore") as f:
                contenu = f.read()

            # Extraire le texte des propriétés Command="..."
            matchs = re.findall(r'(?:Command|command)="([^"]*)"', contenu)
            
            # Ne garder que les lignes non vides
            lignes_propres = [m.strip() for m in matchs if m.strip()]

            # 3. Réécrire seulement s'il y avait des lignes vides en trop
            if len(lignes_propres) < len(matchs):
                print(f"🧹 Nettoyage Macro {num} « {nom} » : {len(matchs)} lignes ➔ {len(lignes_propres)} lignes")
                reecrire_macro_propre(num, nom, lignes_propres)
                compteur += 1
        except Exception as e:
            print(f"⚠️ Erreur lors du traitement de la Macro {num} : {e}")

    print(f"\n✅ Nettoyage terminé ! {compteur} macro(s) réécrite(s) proprement.")


if __name__ == "__main__":
    print("========================================================")
    print("   NETTOYEUR RAPIDE DE MACROS GRANDMA3")
    print("========================================================")
    
    s = input("Numéro de début (Entrée pour TOUTES) : ").strip()
    e = input("Numéro de fin (Entrée pour TOUTES) : ").strip()

    start = int(s) if s.isdigit() else None
    end = int(e) if e.isdigit() else None

    nettoyer_toutes_les_macros(start, end)