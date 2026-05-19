import torch
import torch.nn as nn
import numpy as np
import json
import cv2
import sys
import os
import math

sys.path.insert(0, './MotionBERT')

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions, RunningMode

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir  = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

sys.path.append(os.path.abspath("MotionBERT"))
from lib.utils.tools import get_config
from lib.model.DSTformer import DSTformer

# ── Joints H36M (après conversion mediapipe_to_h36m) ─────────────────────────
#   0=pelvis  7=spine  8=thorax  9=neck  10=head
#   11=lshoulder 12=lelbow 13=lwrist
#   14=rshoulder 15=relbow 16=rwrist

BONE_MAP = {
    # Bras : segment proximal → distal
    "CC_Base_L_Upperarm_052": (11, 12),
    "CC_Base_L_Forearm_053":  (12, 13),
    "CC_Base_R_Upperarm_080": (14, 15),
    "CC_Base_R_Forearm_081":  (15, 16),
    "CC_Base_Head_040":       ( 9, 10),
}

# Ces bones utilisent compute_clavicle_rotation() au lieu de quat_from_two_vecs()
CLAVICLE_BONES = {"CC_Base_L_Clavicle_051", "CC_Base_R_Clavicle_079"}

# ── Conversion H36M → Blender ─────────────────────────────────────────────────
def h36m_to_blender(v):
    # H36M (espace caméra) : X droite (miroir), Y haut, Z vers caméra
    # Blender : X droite, Y profondeur, Z haut
    # → inverser X pour corriger le miroir caméra
    return np.array([-v[0], v[2], v[1]])

# ── Utilitaires quaternions ───────────────────────────────────────────────────
def vec_norm(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-6 else v

def quat_from_two_vecs(a, b):
    """Quaternion minimal qui tourne du vecteur a vers le vecteur b."""
    a, b = vec_norm(a), vec_norm(b)
    dot  = float(np.clip(np.dot(a, b), -1.0, 1.0))
    axis = np.cross(a, b)
    n    = np.linalg.norm(axis)
    if n < 1e-6:
        if dot > 0.999:
            return (1., 0., 0., 0.)
        perp = np.cross(a, [1., 0., 0.])
        if np.linalg.norm(perp) < 1e-6:
            perp = np.cross(a, [0., 1., 0.])
        perp = vec_norm(perp)
        return (0., float(perp[0]), float(perp[1]), float(perp[2]))
    axis /= n
    ang = math.acos(dot)
    s   = math.sin(ang / 2)
    return (math.cos(ang / 2), float(axis[0]*s), float(axis[1]*s), float(axis[2]*s))

def quat_norm_dict(q):
    w, x, y, z = q
    n = math.sqrt(w*w + x*x + y*y + z*z)
    if n < 1e-6:
        return {"w": 1., "x": 0., "y": 0., "z": 0.}
    return {"w": round(w/n, 7), "x": round(x/n, 7),
            "y": round(y/n, 7), "z": round(z/n, 7)}


# ── Rotation clavicule (décomposition anatomique) ─────────────────────────────
def build_thorax_frame(thorax_pos, shoulder_left, shoulder_right):
    """Retourne (axe_x, axe_y, axe_z) repère local du thorax."""
    # Axe latéral : de l'épaule gauche vers la droite
    z_axis = vec_norm(shoulder_right - shoulder_left)
    # Axe vertical : global (on pourrait aussi utiliser thorax-pelvis)
    y_axis = np.array([0., 1., 0.])
    # Axe sagittal : perpendiculaire aux deux
    x_axis = vec_norm(np.cross(y_axis, z_axis))
    return x_axis, y_axis, z_axis

def decompose_vector_in_thorax_frame(vec, x_axis, y_axis, z_axis):
    """Décompose un vecteur dans le repère local."""
    return np.array([np.dot(vec, x_axis),
                     np.dot(vec, y_axis),
                     np.dot(vec, z_axis)])

def compute_clavicle_rotation_motionbert(thorax_pos, shoulder_pos,
                                          shoulder_left, shoulder_right,
                                          ref_dir_local):
    """
    Calcule la rotation relative de la clavicule en utilisant le repère du thorax.
    ref_dir_local : vecteur de référence (thorax->épaule) dans le repère local
                    (généralement issu de la calibration).
    """
    # Construire le repère local du thorax à partir des deux épaules
    x_axis, y_axis, z_axis = build_thorax_frame(thorax_pos, shoulder_left, shoulder_right)

    # Vecteur actuel dans le monde puis dans le repère local
    current_world = vec_norm(shoulder_pos - thorax_pos)
    current_local = decompose_vector_in_thorax_frame(current_world, x_axis, y_axis, z_axis)

    # Référence (typiquement [0, -1, 0] ou calibrée)
    ref_local = ref_dir_local

    # Angle d'élévation (dans le plan sagittal X-Y) : projection sur (X,Y)
    ref_xy = vec_norm(ref_local[[0,1]])
    cur_xy = vec_norm(current_local[[0,1]])
    if np.linalg.norm(ref_xy) > 0 and np.linalg.norm(cur_xy) > 0:
        dot_el = float(np.clip(np.dot(ref_xy, cur_xy), -1., 1.))
        ang_el = math.acos(dot_el)
        # signe : produit vectoriel sur Z (ref_xy × cur_xy) donne le sens
        cross_z = ref_xy[0]*cur_xy[1] - ref_xy[1]*cur_xy[0]
        if cross_z < 0:
            ang_el = -ang_el
    else:
        ang_el = 0.

    # Angle de protraction (dans le plan horizontal X-Z) : projection sur (X,Z)
    ref_xz = vec_norm(ref_local[[0,2]])
    cur_xz = vec_norm(current_local[[0,2]])
    if np.linalg.norm(ref_xz) > 0 and np.linalg.norm(cur_xz) > 0:
        dot_pr = float(np.clip(np.dot(ref_xz, cur_xz), -1., 1.))
        ang_pr = math.acos(dot_pr)
        # signe : produit vectoriel sur Y (ref_xz × cur_xz)
        cross_y = ref_xz[0]*cur_xz[1] - ref_xz[1]*cur_xz[0]  # attention, indices? En fait pour XZ, le cross donne une valeur sur Y
        # Ici on utilise le déterminant 2D : ref_xz[0]*cur_xz[1] - ref_xz[1]*cur_xz[0]
        # qui donne le sinus de l'angle orienté.
        if cross_y < 0:
            ang_pr = -ang_pr
    else:
        ang_pr = 0.

    # Composition des quaternions : rotation autour de Y (protraction) puis autour de X (élévation)
    # Ordre : on applique d'abord l'élévation (autour de X), puis la protraction (autour de Y)
    # En quaternion, q = q_y(ang_pr) * q_x(ang_el)
    half_el = ang_el / 2.
    half_pr = ang_pr / 2.
    q_x = (math.cos(half_el), math.sin(half_el), 0., 0.)
    q_y = (math.cos(half_pr), 0., math.sin(half_pr), 0.)
    # Multiplication q_y * q_x
    w1, x1, y1, z1 = q_y
    w2, x2, y2, z2 = q_x
    qw = w1*w2 - x1*x2 - y1*y2 - z1*z2
    qx = w1*x2 + x1*w2 + y1*z2 - z1*y2
    qy = w1*y2 - x1*z2 + y1*w2 + z1*x2
    qz = w1*z2 + x1*y2 - y1*x2 + z1*w2
    return quat_norm_dict((qw, qx, qy, qz))


# ── Chargement MotionBERT ─────────────────────────────────────────────────────
def load_motionbert(config_path, checkpoint_path):
    cfg = get_config(config_path)
    cfg.norm_layer = nn.LayerNorm

    defaults = {
        'dim_feat': 256, 'dim_rep': 512, 'depth': 5,
        'num_heads': 8,  'mlp_ratio': 4, 'maxlen': 243,
    }
    for key, val in defaults.items():
        if not hasattr(cfg, key):
            setattr(cfg, key, val)

    model = DSTformer(
        dim_in=3, dim_out=3,
        dim_feat=cfg.dim_feat, dim_rep=cfg.dim_rep,
        depth=cfg.depth,       num_heads=cfg.num_heads,
        mlp_ratio=cfg.mlp_ratio, norm_layer=cfg.norm_layer,
        maxlen=cfg.maxlen,
    )

    ckpt = torch.load(checkpoint_path, map_location='cpu')
    state_dict = ckpt.get('model_pos', ckpt)
    new_sd = {(k[7:] if k.startswith('module.') else k): v
              for k, v in state_dict.items()}
    model.load_state_dict(new_sd, strict=False)
    model.eval()
    print("✅ MotionBERT chargé")
    return model, cfg


# ── Extraction 2D MediaPipe → H36M ───────────────────────────────────────────
def mediapipe_to_h36m(landmarks_list, width, height):
    """
    Convertit les 33 landmarks MediaPipe → 17 joints H36M.
    Retourne un array (17, 2) normalisé [0,1].
    """
    lm = landmarks_list

    def pt(idx):
        return np.array([lm[idx].x, lm[idx].y])

    hip_mid      = (pt(23) + pt(24)) / 2
    shoulder_mid = (pt(11) + pt(12)) / 2
    spine        = (hip_mid + shoulder_mid) / 2

    joints = np.zeros((17, 2), dtype=np.float32)
    joints[0]  = hip_mid          # root/pelvis
    joints[1]  = pt(24)           # right_hip
    joints[2]  = pt(26)           # right_knee
    joints[3]  = pt(28)           # right_ankle
    joints[4]  = pt(23)           # left_hip
    joints[5]  = pt(25)           # left_knee
    joints[6]  = pt(27)           # left_ankle
    joints[7]  = spine            # spine
    joints[8]  = shoulder_mid     # thorax  ← pivot des clavicules
    joints[9]  = shoulder_mid     # neck (approximation)
    joints[10] = pt(0)            # head (nez)
    joints[11] = pt(11)           # left_shoulder
    joints[12] = pt(13)           # left_elbow
    joints[13] = pt(15)           # left_wrist
    joints[14] = pt(12)           # right_shoulder
    joints[15] = pt(14)           # right_elbow
    joints[16] = pt(16)           # right_wrist

    return joints  # (17, 2)


# ── Pipeline principal ────────────────────────────────────────────────────────
def extraire_animation_motionbert(
        video_path,
        pose_initiale_path,
        output_path,
        mot,
        config_path     = 'MotionBERT/configs/pose3d/MB_ft_h36m.yaml',
        checkpoint_path = 'checkpoint/pose3d/FT_MB_release_MB_ft_h36m.pth',
        fps_export      = 12,
        window_size     = 243,
        nb_frames_calib = 5,
):
    model_mb, cfg_mb = load_motionbert(config_path, checkpoint_path)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model_mb = model_mb.to(device)

    with open(pose_initiale_path) as f:
        pose_initiale = json.load(f)

    options = PoseLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path='pose_landmarker.task'),
        running_mode=RunningMode.VIDEO,
        num_poses=1,
        output_segmentation_masks=False,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    cap       = cv2.VideoCapture(video_path)
    video_fps = cap.get(cv2.CAP_PROP_FPS) or 25
    n_frames  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duree     = n_frames / video_fps
    print(f"📹 {video_fps:.1f}fps — {n_frames} frames — {duree:.2f}s")
    print(f"   Étape 1 : extraction 2D (toutes les frames)...")

    # ── Étape 1 : extraction 2D sur TOUTES les frames ─────────────────────────
    all_kp2d  = []
    all_times = []

    with PoseLandmarker.create_from_options(options) as landmarker:
        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            h, w   = frame.shape[:2]
            rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            ts_ms  = int(frame_idx * 1000 / video_fps)

            det = landmarker.detect_for_video(mp_img, ts_ms)

            if det.pose_landmarks:
                kp = mediapipe_to_h36m(det.pose_landmarks[0], w, h)
            else:
                kp = all_kp2d[-1] if all_kp2d else np.zeros((17, 2))

            all_kp2d.append(kp)
            all_times.append(frame_idx / video_fps)
            frame_idx += 1

    cap.release()
    N_total = len(all_kp2d)
    print(f"   {N_total} frames 2D extraites")

    # ── Étape 2 : lift 2D → 3D avec MotionBERT ────────────────────────────────
    print("   Étape 2 : lift 2D → 3D (MotionBERT)...")

    kp_array = np.stack(all_kp2d, axis=0)              # (N, 17, 2)
    kp_input = np.zeros((N_total, 17, 3), dtype=np.float32)
    kp_input[:, :, 0] = kp_array[:, :, 0] * 2 - 1
    kp_input[:, :, 1] = kp_array[:, :, 1] * 2 - 1
    kp_input[:, :, 2] = 1.0

    poses_3d = np.zeros((N_total, 17, 3), dtype=np.float32)
    half     = window_size // 2

    for i in range(N_total):
        start  = max(0, i - half)
        end    = min(N_total, i + half + 1)
        window = kp_input[start:end]

        pad_l = half - (i - start)
        pad_r = window_size - len(window) - pad_l
        if pad_l > 0 or pad_r > 0:
            window = np.pad(window, ((pad_l, pad_r), (0,0), (0,0)), mode='edge')

        inp = torch.from_numpy(window[None]).to(device)
        with torch.no_grad():
            out = model_mb(inp)

        poses_3d[i] = out[0, half].cpu().numpy()

        if i % 50 == 0:
            print(f"   frame {i}/{N_total}", end='\r')

    print(f"\n   {N_total} poses 3D reconstruites")

    # Convertir en espace Blender
    poses_bl = np.array([
        [h36m_to_blender(poses_3d[i, j]) for j in range(17)]
        for i in range(N_total)
    ])

    # ── Étape 3 : calibration sur les N premières frames ──────────────────────
    print(f"   Étape 3 : calibration sur {nb_frames_calib} frames...")

    calibration = {}       # pour les autres bones (vecteur monde)
    calib_local_clav = {}  # pour les clavicules (vecteur local)

    for bone_name, (ia, ib) in BONE_MAP.items():
        if bone_name in CLAVICLE_BONES:
            local_vecs = []
            for fi in range(min(nb_frames_calib, N_total)):
                thorax = poses_bl[fi, 8]          # joint thorax (index 8)
                shoulder = poses_bl[fi, ib]       # épaule correspondante
                sh_l = poses_bl[fi, 11]           # épaule gauche (index 11)
                sh_r = poses_bl[fi, 14]           # épaule droite (index 14)
                # Construire repère local du thorax pour cette frame
                x_axis, y_axis, z_axis = build_thorax_frame(thorax, sh_l, sh_r)
                v_world = vec_norm(shoulder - thorax)
                v_local = decompose_vector_in_thorax_frame(v_world, x_axis, y_axis, z_axis)
                local_vecs.append(v_local)
            if local_vecs:
                calib_local_clav[bone_name] = vec_norm(np.mean(local_vecs, axis=0))
            else:
                calib_local_clav[bone_name] = np.array([0., -1., 0.])
        else:
            vecs = []
            for fi in range(min(nb_frames_calib, N_total)):
                d = poses_bl[fi, ib] - poses_bl[fi, ia]
                if np.linalg.norm(d) > 1e-6:
                    vecs.append(vec_norm(d))
            if vecs:
                calibration[bone_name] = vec_norm(np.mean(vecs, axis=0))
            else:
                calibration[bone_name] = np.array([0., -1., 0.])

    # ── Étape 4 : sous-échantillonnage + calcul des rotations ─────────────────
    print("   Étape 4 : calcul des rotations...")

    step      = max(1, int(round(video_fps / fps_export)))
    keyframes = []

    for i in range(0, N_total, step):
        t     = all_times[i]
        bones = {}

        for bone_name, (ia, ib) in BONE_MAP.items():
            d_calib = calibration[bone_name]

            if bone_name in CLAVICLE_BONES:
                thorax = poses_bl[i, 8]
                shoulder = poses_bl[i, ib]
                sh_l = poses_bl[i, 11]
                sh_r = poses_bl[i, 14]
                ref_local = calib_local_clav.get(bone_name, np.array([0., -1., 0.]))
                q_rel = compute_clavicle_rotation_motionbert(
                    thorax, shoulder, sh_l, sh_r, ref_local
                )
            else:
                d_current = vec_norm(poses_bl[i, ib] - poses_bl[i, ia])
                d_calib = calibration[bone_name]
                q_rel = quat_norm_dict(quat_from_two_vecs(d_calib, d_current))

            bones[bone_name] = {"rotation": q_rel}

        keyframes.append({"time": round(float(t), 4), "bones": bones})

    print(f"\n✅ {len(keyframes)} keyframes extraites")

    out = {
        "mot":       mot,
        "source":    "MotionBERT",
        "fps":       fps_export,
        "duration":  duree,
        "nb_frames": len(keyframes),
        "keyframes": keyframes,
    }
    with open(output_path, 'w') as f:
        json.dump(out, f, indent=2)

    print(f"💾 {output_path}  ({os.path.getsize(output_path)//1024} Ko)")
    return output_path


# ── Lancement ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--video',      required=True)
    parser.add_argument('--output',     default='output.json')
    parser.add_argument('--mot',        default='signe')
    parser.add_argument('--config',     default='./MotionBERT/configs/pose3d/MB_ft_h36m.yaml')
    parser.add_argument('--checkpoint', default='./MotionBERT/checkpoint/pose3d/FT_MB_release_MB_ft_h36m.pth')
    parser.add_argument('--fps',        type=int, default=12)
    parser.add_argument('--calib',      type=int, default=5)
    args = parser.parse_args()

    extraire_animation_motionbert(
        video_path         = args.video,
        pose_initiale_path = "/Users/gaspardc/Documents/CPE Lyon/4A/PT/perso/pose_initiale.json",
        output_path        = args.output,
        mot                = args.mot,
        config_path        = args.config,
        checkpoint_path    = args.checkpoint,
        fps_export         = args.fps,
        nb_frames_calib    = args.calib,
    )