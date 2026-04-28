# extract_landmarks.py
import cv2
import mediapipe as mp
import numpy as np
import json

mp_holistic = mp.solutions.holistic

def extraire_landmarks_video(chemin_video):
    """
    Extrait les landmarks MediaPipe frame par frame depuis une vidéo.
    Retourne une liste de vecteurs normalisés (un par frame).
    """
    cap = cv2.VideoCapture(chemin_video)
    frames_landmarks = []

    with mp_holistic.Holistic(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5
    ) as holistic:

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = holistic.process(rgb)

            vecteur = extraire_vecteur(results)
            if vecteur is not None:
                frames_landmarks.append(vecteur)

    cap.release()
    return np.array(frames_landmarks)  # shape: (nb_frames, nb_features)


def extraire_vecteur(results):
    """
    Construit un vecteur de features à partir des landmarks détectés.
    On prend : pose (bras/épaules) + mains gauche + mains droite
    """
    def landmarks_to_array(landmarks, n):
        if landmarks:
            return np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark[:n]]).flatten()
        return np.zeros(n * 3)

    # Pose : on garde seulement les points utiles (épaules, coudes, poignets)
    # Indices MediaPipe Pose : 11,12 épaules | 13,14 coudes | 15,16 poignets
    pose = np.zeros(6 * 3)
    if results.pose_landmarks:
        indices_utiles = [11, 12, 13, 14, 15, 16]
        pose = np.array([
            [results.pose_landmarks.landmark[i].x,
             results.pose_landmarks.landmark[i].y,
             results.pose_landmarks.landmark[i].z]
            for i in indices_utiles
        ]).flatten()

    main_gauche  = landmarks_to_array(results.left_hand_landmarks,  21)
    main_droite  = landmarks_to_array(results.right_hand_landmarks, 21)

    return np.concatenate([pose, main_gauche, main_droite])
    # Taille finale : 18 + 63 + 63 = 144 valeurs par frame