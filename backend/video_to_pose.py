# video_to_pose_json.py
import cv2
import mediapipe as mp
import numpy as np
import json
from mapping import MAPPING_MEDIAPIPE_CC4

mp_holistic = mp.solutions.holistic

def vecteur_vers_quaternion(v_from, v_to):
    """
    Calcule le quaternion de rotation entre deux vecteurs directeurs.
    C'est le cœur de la conversion MediaPipe → bone rotation.
    """
    v_from = v_from / (np.linalg.norm(v_from) + 1e-8)
    v_to   = v_to   / (np.linalg.norm(v_to)   + 1e-8)

    dot = np.clip(np.dot(v_from, v_to), -1.0, 1.0)
    cross = np.cross(v_from, v_to)
    cross_norm = np.linalg.norm(cross)

    if cross_norm < 1e-8:
        # Vecteurs parallèles
        if dot > 0:
            return {"w": 1.0, "x": 0.0, "y": 0.0, "z": 0.0}
        else:
            return {"w": 0.0, "x": 0.0, "y": 1.0, "z": 0.0}

    angle = np.arccos(dot)
    axis  = cross / cross_norm
    s = np.sin(angle / 2)

    return {
        "w": float(np.cos(angle / 2)),
        "x": float(axis[0] * s),
        "y": float(axis[1] * s),
        "z": float(axis[2] * s)
    }


def landmarks_to_array(landmarks):
    """Convertit les landmarks MediaPipe en tableau numpy (N, 3)."""
    return np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])


def extraire_pose_frame(results, rest_pose):
    """
    Convertit les résultats MediaPipe d'une frame en dictionnaire
    de quaternions compatibles avec ton format JSON Blender.
    """
    # Partir de la rest pose comme base
    pose_frame = {k: dict(v) for k, v in rest_pose.items()}

    pose_lm   = landmarks_to_array(results.pose_landmarks)   if results.pose_landmarks   else None
    main_g_lm = landmarks_to_array(results.left_hand_landmarks)  if results.left_hand_landmarks  else None
    main_d_lm = landmarks_to_array(results.right_hand_landmarks) if results.right_hand_landmarks else None

    for bone_name, config in MAPPING_MEDIAPIPE_CC4.items():

        # ── Bras (landmarks pose) ──────────────────────────────
        if "point_proximal" in config and pose_lm is not None:
            p = pose_lm[config["point_proximal"]]
            d = pose_lm[config["point_distal"]]
            vecteur = d - p

            # Direction de repos du bone (axe Y local standard CC4)
            v_repos = np.array([0.0, 1.0, 0.0])
            q = vecteur_vers_quaternion(v_repos, vecteur)
            pose_frame[bone_name] = q

        # ── Doigts (landmarks main) ────────────────────────────
        elif "main" in config:
            lm = main_g_lm if config["main"] == "gauche" else main_d_lm
            if lm is None:
                continue
            p = lm[config["proximal"]]
            d = lm[config["distal"]]
            vecteur = d - p

            v_repos = np.array([0.0, 1.0, 0.0])
            q = vecteur_vers_quaternion(v_repos, vecteur)
            pose_frame[bone_name] = q

    return pose_frame


def video_vers_json(chemin_video, chemin_rest_pose, chemin_sortie, fps_cible=24):
    """
    Pipeline complet : vidéo → séquence de poses JSON
    compatibles avec ton script apply_pose_from_json.
    """
    # Charger la rest pose (ton fichier LSF_Bonjour_F1_neutre.json)
    with open(chemin_rest_pose, 'r') as f:
        rest_pose = json.load(f)

    cap = cv2.VideoCapture(chemin_video)
    fps_video = cap.get(cv2.CAP_PROP_FPS)
    intervalle = max(1, int(fps_video / fps_cible))

    sequence = []
    frame_idx = 0

    with mp_holistic.Holistic(
        static_image_mode=False,
        model_complexity=2,              # max précision pour les mains
        min_detection_confidence=0.6,
        min_tracking_confidence=0.5
    ) as holistic:

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Sous-échantillonnage pour atteindre fps_cible
            if frame_idx % intervalle == 0:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = holistic.process(rgb)

                if results.pose_landmarks:
                    pose = extraire_pose_frame(results, rest_pose)
                    sequence.append(pose)

            frame_idx += 1

    cap.release()

    # Sauvegarder la séquence complète
    with open(chemin_sortie, 'w') as f:
        json.dump(sequence, f, indent=2)

    print(f"✅ {len(sequence)} frames exportées → {chemin_sortie}")
    return sequence


# ── Utilisation ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    video_vers_json(
        chemin_video    = "videos_lsf/bonjour.mp4",
        chemin_rest_pose= "LSF_Bonjour_F1_neutre.json",
        chemin_sortie   = "animations/LSF_Bonjour_mediapipe.json"
    )