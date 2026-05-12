"""
auteur: Mehdi ABD ALI
Parcout le dossier static/animation et crée un fichier json avec le chemin de chaque signe 
et son lemme afin d'automatiser la création de la bdd
"""




import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

BUCKET_BASE_URL = os.getenv("BUCKET_BASE_URL")  # ex: https://objectstorage.eu-paris-1.oraclecloud.com/n/NAMESPACE/b/BUCKET/o/
FICHIER_JSON = os.getenv("FICHIER_JSON")


def synchroniser_bdd_depuis_bucket(bucket_base_url, fichier_json):
    """
    Liste les fichiers .glb dans le bucket OCI et génère le JSON correspondant.
    """

    # L'API OCI permet de lister les objets d'un bucket public avec ce endpoint
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

        # On ne garde que les .glb dans le dossier animations
        if not nom.startswith("static/animations/") or not nom.endswith(".glb"):
            continue

        nom_fichier = nom.split("/")[-1]   # ex: BONJOUR.glb
        nom_brut = nom_fichier.replace(".glb", "")

        if nom_brut.lower() == "avatar_base":
            continue

        lemme = nom_brut.upper().replace(" ", "_").replace("-", "_")

        entree = {
            "lemme": lemme,
            "fichier_3d": nom  # chemin relatif : static/animations/BONJOUR.glb
        }

        base_de_donnees.append(entree)
        print("-", lemme)

    with open(fichier_json, 'w', encoding='utf-8') as f:
        json.dump(base_de_donnees, f, indent=4, ensure_ascii=False)

    print(f"{len(base_de_donnees)} animations ajoutées dans {fichier_json}")


if __name__ == "__main__":
    print("Mots ajoutés :")
    synchroniser_bdd_depuis_bucket(BUCKET_BASE_URL, FICHIER_JSON)