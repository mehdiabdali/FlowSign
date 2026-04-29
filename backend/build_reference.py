# build_reference_db.py
import numpy as np
import json
import os
from extract import extraire_landmarks_video

def resample_sequence(sequence, target_len=40):
    """
    Rééchantillonne une séquence à une longueur fixe (interpolation).
    Nécessaire pour comparer des vidéos de durées différentes.
    """
    indices = np.linspace(0, len(sequence) - 1, target_len)
    return np.array([sequence[int(i)] for i in indices])

def construire_bdd_reference(dossier_videos, fichier_sortie="reference_landmarks.json"):
    """
    Pour chaque vidéo dans le dossier, extrait les landmarks
    et les stocke comme référence pour la reconnaissance.
    """
    bdd = {}

    for fichier in os.listdir(dossier_videos):
        if not fichier.endswith(".mp4"):
            continue

        lemme = fichier.replace(".mp4", "").upper()
        chemin = os.path.join(dossier_videos, fichier)

        print(f"Traitement de {lemme}...")
        landmarks = extraire_landmarks_video(chemin)

        if len(landmarks) == 0:
            print(f"  ⚠️ Aucun landmark détecté pour {lemme}")
            continue

        # Normalisation à 40 frames
        sequence = resample_sequence(landmarks, target_len=40)
        bdd[lemme] = sequence.tolist()
        print(f"  ✅ {lemme} : {len(landmarks)} frames → normalisé à 40")

    with open(fichier_sortie, 'w') as f:
        json.dump(bdd, f)

    print(f"\n✅ BDD de référence créée : {len(bdd)} signes")

construire_bdd_reference("videos_lsf/", "reference_landmarks.json")