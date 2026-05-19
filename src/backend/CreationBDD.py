"""
auteur: Mehdi ABD ALI
Parcourt le dossier animation dans le bucket OCI et crée un fichier json avec le chemin de chaque signe 
et son lemme afin d'automatiser la création de la base de données.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

BUCKET_BASE_URL = os.getenv("BUCKET_BASE_URL")  
FICHIER_JSON = os.getenv("FICHIER_JSON")

def synchroniser_bdd_depuis_bucket(bucket_base_url, fichier_json):
    # L'API d'Oracle permet de lister les objets d'un bucket public via ce endpoint
    url_liste = bucket_base_url.rstrip("/") + "?fields=name"

    print(f"Connexion au bucket : {url_liste}")
    reponse = requests.get(url_liste)

    if reponse.status_code != 200:
        print(f"Erreur lors de la connexion au bucket (status {reponse.status_code})")
        return

    data = reponse.json()
    objets = data.get("items", [])
    base_de_donnees = []

    for objet in objets:
        nom = objet.get("name", "")

        # On filtre pour ne garder que les modèles 3D du dossier animations
        if not nom.startswith("static/animations/") or not nom.endswith(".glb"):
            continue

        # Extraction du nom du fichier pour créer le mot-clé (lemme)
        nom_fichier = nom.split("/")[-1]   
        nom_brut = nom_fichier.replace(".glb", "")

        # L'avatar de base n'est pas un signe, on l'ignore
        if nom_brut.lower() == "avatar_base":
            continue

        # Formatage propre du lemme (tout en majuscules, sans espaces)
        lemme = nom_brut.upper().replace(" ", "_").replace("-", "_")

        entree = {
            "lemme": lemme,
            "fichier_3d": nom  
        }

        base_de_donnees.append(entree)
        print("-", lemme)

    # Sauvegarde des résultats dans un fichier local pour la prochaine étape
    with open(fichier_json, 'w', encoding='utf-8') as f:
        json.dump(base_de_donnees, f, indent=4, ensure_ascii=False)

    print(f"{len(base_de_donnees)} animations ajoutées dans {fichier_json}")

if __name__ == "__main__":
    print("Mots ajoutés :")
    synchroniser_bdd_depuis_bucket(BUCKET_BASE_URL, FICHIER_JSON)