import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from trad import traduire_vers_lsf
from recognize import reconnaitre_signe
import tempfile, os



def api_reconnaitre():
    if 'video' not in request.files:
        return jsonify({"erreur": "Vidéo manquante"}), 400

    video = request.files['video']

    # Sauvegarde temporaire
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        video.save(tmp.name)
        chemin_tmp = tmp.name

    lemme, score = reconnaitre_signe(chemin_tmp)
    os.unlink(chemin_tmp)  # Nettoyage

    if lemme is None:
        return jsonify({"erreur": "Signe non reconnu", "score": score}), 404

    # Chercher le GLB correspondant
    signe = collection.find_one({"lemme": lemme})
    return jsonify({
        "lemme": lemme,
        "score": score,
        "fichier_3d": signe['fichier_3d'] if signe else None
    }), 200




app = Flask(__name__)
CORS(app)

# 1. On prépare la connexion à MongoDB
load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client['flowsign_db']
collection = db['signes']

@app.route('/api/traduire', methods=['POST'])
def api_traduire():
    data = request.get_json()
    
    if not data or 'texte' not in data:
        return jsonify({"erreur": "Texte manquant"}), 400
    
    # 2. On traduit la phrase en mots LSF (ex: ["MON_TEST"])
    mots_lsf = traduire_vers_lsf(data['texte'])
    
    # 3. On cherche les fichiers 3D correspondants dans la base
    chemins_animations = []
    mots_sans_animation = []
    for mot in mots_lsf:
        # On cherche le document où le lemme correspond exactement
        signe = collection.find_one({"lemme": mot})
        if signe:
            chemins_animations.append(signe['fichier_3d'])
        else:
            mots_sans_animation.append(mot)
    traduction_complete = len(mots_sans_animation) == 0
    # 4. On renvoie les chemins, c'est ça que Three.js attend
    return jsonify({"fichiers_glb": chemins_animations,
                    "mots_traduits": mots_lsf,
                    "mots_sans_animation": mots_sans_animation,
                    "traduction_complete": traduction_complete}), 200


@app.route('/api/dictionnaire', methods=['GET', 'OPTIONS'])
def obtenir_dictionnaire():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        # On demande à MongoDB de nous donner tous les signes
        # Le {"_id": 0, "lemme": 1} signifie : ne me renvoie pas l'ID technique, juste le lemme
        # Le .sort("lemme", 1) permet de trier par ordre alphabétique (A-Z)
        signes = list(collection.find({}, {"_id": 0, "lemme": 1}).sort("lemme", 1))
        
        # On extrait juste les textes pour faire une liste simple
        liste_mots = [signe["lemme"] for signe in signes]
        
        return jsonify({"mots": liste_mots}), 200
    except Exception as e:
        print("Erreur dictionnaire :", e)
        return jsonify({"erreur": "Impossible de charger le dictionnaire"}), 500

if __name__ == '__main__':
    print("Serveur API FlowSign démarré sur http://127.0.0.1:5000")
    app.run(debug=True, port=5000)