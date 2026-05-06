import json
import os
from dotenv import load_dotenv
from pymongo import MongoClient

def remplir_base_depuis_json(chemin_fichier_json):
    try:
        load_dotenv()
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client['flowsign_db']
        collection = db['signes']
    except Exception as e:
        print(f"Erreur de connexion à MongoDB : {e}")
        return

    print(f"Lecture du fichier : {chemin_fichier_json}...")
    try:
        with open(chemin_fichier_json, 'r', encoding='utf-8') as fichier:
            donnees_a_inserer = json.load(fichier)
    except FileNotFoundError:
        print(f"Erreur : Le fichier {chemin_fichier_json} est introuvable.")
        return
    except json.JSONDecodeError:
        print(f"Erreur : Le fichier {chemin_fichier_json} est mal formaté.")
        return

    if not donnees_a_inserer:
        print("Le fichier JSON est vide.")
        return

    compteur = 0
    for doc in donnees_a_inserer:
        collection.update_one(
            {"lemme": doc["lemme"]},
            {"$set": doc},
            upsert=True
        )
        compteur += 1

    print(f"Succès ! {compteur} signes mis à jour dans MongoDB.")

if __name__ == "__main__":
    fichier_source_json = "bdd_lsf.json"
    remplir_base_depuis_json(fichier_source_json)