"""
Lit le fichier JSON généré et met à jour la base de données MongoDB.
Utilise la méthode upsert pour éviter les doublons lors des mises à jour.
"""

import json
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pathlib import Path

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "flowsign_db"
COLLECTION_NAME = "signes"
DOSSIER_ANIMATIONS = os.getenv("DOSSIER_ANIMATIONS")
FICHIER_JSON = os.getenv("FICHIER_JSON")

def remplir_base_depuis_json(chemin_fichier_json):
    try:
        # Initialisation de la connexion à la base de données
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
    except Exception as e:
        print(f"Erreur de connexion à MongoDB : {e}")
        return

    print(f"Lecture du fichier : {chemin_fichier_json}...")
    
    # Sécurisation de la lecture du fichier
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
        # L'upsert met à jour le document s'il existe, ou le crée s'il n'existe pas
        collection.update_one(
            {"lemme": doc["lemme"]},
            {"$set": doc},
            upsert=True
        )
        # Création d'un index pour accélérer les futures recherches par mot
        collection.create_index("lemme", unique=True)
        compteur += 1

    print(f"Succès ! {compteur} signes mis à jour dans MongoDB.")

if __name__ == "__main__":
    remplir_base_depuis_json(FICHIER_JSON)