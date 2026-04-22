from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from trad import traduire_vers_lsf

app = Flask(__name__)
CORS(app)

# 1. On prépare la connexion à MongoDB
client = MongoClient('mongodb://localhost:27017/')
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
        # On cherche le document où le gloss correspond exactement
        signe = collection.find_one({"gloss": mot})
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

if __name__ == '__main__':
    print("Serveur API FlowSign démarré sur http://127.0.0.1:5000")
    app.run(debug=True, port=5000)