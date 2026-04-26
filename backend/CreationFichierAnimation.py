import json
from pathlib import Path

def synchroniser_bdd_depuis_fichiers(dossier_animations, fichier_sortie_json):
    """
    Scanne le dossier des animations et génère la base de données JSON correspondante.
    """
    chemin_dossier = Path(dossier_animations)
    
    base_de_donnees = []
    
    # On cherche tous les fichiers .glb dans le dossier
    fichiers_glb = list(chemin_dossier.glob("*.glb"))
    
    for fichier in fichiers_glb:
        # stem récupère le nom sans l'extension (ex: 'bonjour' pour 'bonjour.glb')
        nom_brut = fichier.stem

        if nom_brut.lower() == "avatar_base":
            continue
        
        # On crée le gloss en majuscules (ex: 'BONJOUR')
        # On remplace aussi les espaces ou tirets par des underscores par sécurité
        gloss = nom_brut.upper().replace(" ", "_").replace("-", "_")
        
        # Construction de l'entrée pour le JSON
        entree = {
            "gloss": gloss,
            "fichier_3d": f"static/animations/{fichier.name}"
        }
        
        base_de_donnees.append(entree)
        print("-", gloss)

    # Sauvegarde finale
    with open(fichier_sortie_json, 'w', encoding='utf-8') as f:
        json.dump(base_de_donnees, f, indent=4, ensure_ascii=False)

    print(f" {len(base_de_donnees)} animations ajouté dans {fichier_sortie_json}")

# --- CONFIGURATION ---
if __name__ == "__main__":
    # Chemin vers  dossier d'animations 
    dossier_source = "../frontend/static/animations"
    # Nom du fichier JSON 
    destination_json = "bdd_lsf.json"
    print("mot ajouté:")
    synchroniser_bdd_depuis_fichiers(dossier_source, destination_json)