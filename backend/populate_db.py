import json
from pymongo import MongoClient

def remplir_base_depuis_json(chemin_fichier_json):
    # 1. Connexion à MongoDB
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['flowsign_db']
        collection = db['signes']
    except Exception as e:
        print(f"Erreur de connexion à MongoDB : {e}")
        return

    # 2. Ouverture et lecture du fichier JSON
    print(f"Lecture du fichier : {chemin_fichier_json}...")
    try:
        with open(chemin_fichier_json, 'r', encoding='utf-8') as fichier:
            # json.load transforme le texte du fichier en vraie liste Python
            donnees_a_inserer = json.load(fichier)
    except FileNotFoundError:
        print(f"Erreur : Le fichier {chemin_fichier_json} est introuvable.")
        return
    except json.JSONDecodeError:
        print(f"Erreur : Le fichier {chemin_fichier_json} est mal formaté (ce n'est pas du JSON valide).")
        return

    # Vérification de sécurité
    if not donnees_a_inserer:
        print("Le fichier JSON est vide. Rien n'a été modifié dans la base.")
        return

    # 3. Nettoyage de l'ancienne collection
    print("Nettoyage de l'ancienne base de données...")
    collection.delete_many({})

    # 4. Insertion des nouvelles données
    print(f"Insertion de {len(donnees_a_inserer)} signes dans MongoDB...")
    resultat = collection.insert_many(donnees_a_inserer)

    print(f"Succès ! La base a été mise à jour avec {len(resultat.inserted_ids)} signes.")

# --- EXÉCUTION ---
if __name__ == "__main__":
    fichier_source_json = "bdd_lsf.json" 
    
    remplir_base_depuis_json(fichier_source_json)