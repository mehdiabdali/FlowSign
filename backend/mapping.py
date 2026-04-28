# mapping.py
MAPPING_MEDIAPIPE_CC4 = {

    # ── BRAS GAUCHE ────────────────────────────────────────────
    # Vecteur épaule gauche → coude gauche
    "CC_Base_L_Upperarm_052": {
        "point_proximal": 11,   # épaule gauche
        "point_distal":   13,   # coude gauche
    },
    # Vecteur coude gauche → poignet gauche
    "CC_Base_L_Forearm_053": {
        "point_proximal": 13,   # coude gauche
        "point_distal":   15,   # poignet gauche
    },

    # ── BRAS DROIT ─────────────────────────────────────────────
    "CC_Base_R_Upperarm_080": {
        "point_proximal": 12,   # épaule droite
        "point_distal":   14,   # coude droit
    },
    "CC_Base_R_Forearm_081": {
        "point_proximal": 14,   # coude droit
        "point_distal":   16,   # poignet droit
    },

    # ── MAIN GAUCHE (landmarks main séparés) ───────────────────
    "CC_Base_L_Hand_057":    {"main": "gauche", "proximal": 0,  "distal": 9},
    "CC_Base_L_Index1_067":  {"main": "gauche", "proximal": 5,  "distal": 6},
    "CC_Base_L_Index2_068":  {"main": "gauche", "proximal": 6,  "distal": 7},
    "CC_Base_L_Index3_069":  {"main": "gauche", "proximal": 7,  "distal": 8},
    "CC_Base_L_Mid1_064":    {"main": "gauche", "proximal": 9,  "distal": 10},
    "CC_Base_L_Mid2_065":    {"main": "gauche", "proximal": 10, "distal": 11},
    "CC_Base_L_Mid3_066":    {"main": "gauche", "proximal": 11, "distal": 12},
    "CC_Base_L_Ring1_060":   {"main": "gauche", "proximal": 13, "distal": 14},
    "CC_Base_L_Ring2_062":   {"main": "gauche", "proximal": 14, "distal": 15},
    "CC_Base_L_Ring3_063":   {"main": "gauche", "proximal": 15, "distal": 16},
    "CC_Base_L_Pinky1_058":  {"main": "gauche", "proximal": 17, "distal": 18},
    "CC_Base_L_Pinky2_059":  {"main": "gauche", "proximal": 18, "distal": 19},
    "CC_Base_L_Pinky3_060":  {"main": "gauche", "proximal": 19, "distal": 20},
    "CC_Base_L_Thumb1_070":  {"main": "gauche", "proximal": 1,  "distal": 2},
    "CC_Base_L_Thumb2_071":  {"main": "gauche", "proximal": 2,  "distal": 3},
    "CC_Base_L_Thumb3_072":  {"main": "gauche", "proximal": 3,  "distal": 4},

    # ── MAIN DROITE ────────────────────────────────────────────
    "CC_Base_R_Hand_085":    {"main": "droite", "proximal": 0,  "distal": 9},
    "CC_Base_R_Index1_095":  {"main": "droite", "proximal": 5,  "distal": 6},
    "CC_Base_R_Index2_096":  {"main": "droite", "proximal": 6,  "distal": 7},
    "CC_Base_R_Index3_097":  {"main": "droite", "proximal": 7,  "distal": 8},
    "CC_Base_R_Mid1_089":    {"main": "droite", "proximal": 9,  "distal": 10},
    "CC_Base_R_Mid2_090":    {"main": "droite", "proximal": 10, "distal": 11},
    "CC_Base_R_Mid3_091":    {"main": "droite", "proximal": 11, "distal": 12},
    "CC_Base_R_Ring1_086":   {"main": "droite", "proximal": 13, "distal": 14},
    "CC_Base_R_Ring2_087":   {"main": "droite", "proximal": 14, "distal": 15},
    "CC_Base_R_Ring3_088":   {"main": "droite", "proximal": 15, "distal": 16},
    "CC_Base_R_Pinky1_098":  {"main": "droite", "proximal": 17, "distal": 18},
    "CC_Base_R_Pinky2_099":  {"main": "droite", "proximal": 18, "distal": 19},
    "CC_Base_R_Pinky3_0100": {"main": "droite", "proximal": 19, "distal": 20},
    "CC_Base_R_Thumb1_092":  {"main": "droite", "proximal": 1,  "distal": 2},
    "CC_Base_R_Thumb2_093":  {"main": "droite", "proximal": 2,  "distal": 3},
    "CC_Base_R_Thumb3_094":  {"main": "droite", "proximal": 3,  "distal": 4},
}