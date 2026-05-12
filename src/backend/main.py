import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from trad import traduire_vers_lsf
from CreationBDD import synchroniser_bdd_depuis_bucket
from populate_db import remplir_base_depuis_json

# 1. Chargement des variables d'environnement EN PREMIER
load_dotenv()

app = Flask(__name__)
CORS(app)

# 2. Connexion à MongoDB et lecture des variables (après load_dotenv)
client = MongoClient(os.getenv("MONGO_URI"))
db = client['flowsign_db']
collection = db['signes']
DOSSIER_ANIMATIONS = os.getenv("DOSSIER_ANIMATIONS")
FICHIER_JSON = os.getenv("FICHIER_JSON")

# 3. Synchro automatique au démarrage (fonctionne avec Gunicorn ET python main.py)
print("--- Synchronisation de la base de données ---")
synchroniser_bdd_depuis_bucket(DOSSIER_ANIMATIONS, FICHIER_JSON)
remplir_base_depuis_json(FICHIER_JSON)
print("--- Synchronisation terminée ---")


@app.route('/api/traduire', methods=['POST'])
def api_traduire():
    data = request.get_json()

    if not data or 'texte' not in data:
        return jsonify({"erreur": "Texte manquant"}), 400

    # Traduction de la phrase en mots LSF
    mots_lsf = traduire_vers_lsf(data['texte'])

    # Recherche des fichiers 3D correspondants dans la base
    chemins_animations = []
    mots_sans_animation = []
    for mot in mots_lsf:
        signe = collection.find_one({"lemme": mot})
        if signe:
            chemins_animations.append(signe['fichier_3d'])
        else:
            mots_sans_animation.append(mot)

    traduction_complete = len(mots_sans_animation) == 0

    return jsonify({
        "fichiers_glb": chemins_animations,
        "mots_traduits": mots_lsf,
        "mots_sans_animation": mots_sans_animation,
        "traduction_complete": traduction_complete
    }), 200


@app.route('/api/dictionnaire', methods=['GET', 'OPTIONS'])
def obtenir_dictionnaire():
    if request.method == 'OPTIONS':
        return '', 200

    try:
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