from pymongo import MongoClient

def remplir_base():
    # 1. On se connecte à ton container Docker MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    
    # 2. On sélectionne ta base de données (elle se créera toute seule)
    db = client['flowsign_db']
    collection = db['signes']

    # 3. On vide la base avant de la remplir 
    # (ça évite d'avoir les mots en double si tu relances le script pour tester)
    collection.delete_many({})

    # 4. Voici tes données : on fait le lien entre le mot et ton fichier 3D
    donnees_de_depart = [
        {
            "mot": "test1",
            "gloss": "MON_TEST",
            "fichier_3d": "static/animations/MON_TEST.glb",
            "categorie": "Test"
        },
        
        {
            "mot": "merci",
            "gloss": "MERCI",
            "fichier_3d": "static/animations/MERCI.glb",
            "categorie": "Test"
        },

        {
            "mot": "NON",
            "gloss": "NON",
            "fichier_3d": "static/animations/NON.glb",
            "categorie": "Test"
        },

        {
            "mot": "bonjour",
            "gloss": "BONJOUR",
            "fichier_3d": "static/animations/BONJOUR.glb",
            "categorie": "salutation"
        },
        {
            "mot": "JE",
            "gloss": "JE",
            "fichier_3d": "static/animations/JE.glb",
            "categorie": "test"
        }
    
    ]

    # 5. On insère tout d'un coup
    resultat = collection.insert_many(donnees_de_depart)
    print(f"Succès ! La base est remplie avec {len(resultat.inserted_ids)} signes.")

if __name__ == "__main__":
    remplir_base()