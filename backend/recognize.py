# recognize.py
import numpy as np
import json
from extract_landmarks import extraire_landmarks_video, resample_sequence

def dtw_distance(seq1, seq2):
    """
    Dynamic Time Warping — compare deux séquences de longueurs potentiellement
    différentes. Bien adapté aux gestes car deux personnes ne signent pas
    à la même vitesse.
    """
    n, m = len(seq1), len(seq2)
    dtw = np.full((n + 1, m + 1), np.inf)
    dtw[0, 0] = 0

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = np.linalg.norm(seq1[i-1] - seq2[j-1])
            dtw[i, j] = cost + min(dtw[i-1, j], dtw[i, j-1], dtw[i-1, j-1])

    return dtw[n, m]


def reconnaitre_signe(chemin_video, fichier_reference="reference_landmarks.json", seuil=500):
    """
    Compare une vidéo inconnue avec toutes les références en BDD.
    Retourne le lemme reconnu et son score de confiance.
    """
    # Charger la BDD de référence
    with open(fichier_reference, 'r') as f:
        bdd = json.load(f)

    # Extraire les landmarks de la vidéo à reconnaître
    landmarks = extraire_landmarks_video(chemin_video)
    if len(landmarks) == 0:
        return None, 0

    sequence = resample_sequence(landmarks, target_len=30)

    # Comparer avec chaque signe de la BDD
    scores = {}
    for lemme, ref_data in bdd.items():
        ref = np.array(ref_data)
        distance = dtw_distance(sequence, ref)
        scores[lemme] = distance

    # Le signe le plus proche
    meilleur = min(scores, key=scores.get)
    meilleure_distance = scores[meilleur]

    if meilleure_distance > seuil:
        return None, meilleure_distance  # Pas assez confiant

    return meilleur, meilleure_distance