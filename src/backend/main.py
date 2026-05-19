"""
auteur: Mehdi ABD ALI
Serveur backend principal utilisant Flask. 
Expose les routes de l'API, fait le lien entre la traduction linguistique et la base de données.
"""

import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from trad import traduire_vers_lsf
from CreationBDD import synchroniser_bdd_depuis_bucket
from populate_db import remplir_base_depuis_json

# Chargement impératif des variables d'environnement avant toute configuration
load_dotenv()

app = Flask(__name__)
CORS(app)

# Connexion à MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client['flowsign_db']
collection = db['signes']

DOSSIER_ANIMATIONS = os.getenv("BUCKET_BASE_URL")
FICHIER_JSON = os.getenv("FICHIER_JSON")

# Synchronisation automatique de la base au démarrage du conteneur
print("--- Synchronisation de la base de données ---")
synchroniser_bdd_depuis_bucket(DOSSIER_ANIMATIONS, FICHIER_JSON)
remplir_base_depuis_json(FICHIER_JSON)
print("--- Synchronisation terminée ---")

@app.route('/api/traduire', methods=['POST'])
def api_traduire():
    data = request.get_json()

    if not data or 'texte' not in data:
        return jsonify({"erreur": "Texte manquant"}), 400

    # 1. Analyse linguistique via spaCy
    mots_lsf = traduire_vers_lsf(data['texte'])

    # 2. Vérification de la disponibilité des modèles 3D dans MongoDB
    chemins_animations = []
    mots_sans_animation = []
    
    for mot in mots_lsf:
        signe = collection.find_one({"lemme": mot})
        if signe:
            chemins_animations.append(signe['fichier_3d'])
        else:
            mots_sans_animation.append(mot)

    # La traduction est complète si aucun mot ne manque dans la base
    traduction_complete = len(mots_sans_animation) == 0

    return jsonify({
        "fichiers_glb": chemins_animations,
        "mots_traduits": mots_lsf,
        "mots_sans_animation": mots_sans_animation,
        "traduction_complete": traduction_complete
    }), 200

@app.route('/api/dictionnaire', methods=['GET', 'OPTIONS'])
def obtenir_dictionnaire():
    # Gestion des requêtes preflight CORS du navigateur
    if request.method == 'OPTIONS':
        return '', 200

    try:
        # Récupère tous les lemmes de la base de données et les trie par ordre alphabétique
        signes = list(collection.find({}, {"_id": 0, "lemme": 1}).sort("lemme", 1))
        liste_mots = [signe["lemme"] for signe in signes]
        return jsonify({"mots": liste_mots}), 200
    except Exception as e:
        print("Erreur dictionnaire :", e)
        return jsonify({"erreur": "Impossible de charger le dictionnaire"}), 500

if __name__ == '__main__':
    print("--- Démarrage de l'API FlowSign ---")
    print(f"Connexion MongoDB sur : {os.getenv('MONGO_URI')}")
    print("Serveur en écoute sur http://0.0.0.0:5000")
    print("-----------------------------------")
    app.run(host="0.0.0.0", port=5000)