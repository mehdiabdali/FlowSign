# dans video_to_glb.py  —  script de pipeline complet
import subprocess
import os

def pipeline_complet(chemin_video, nom_signe):
    """
    Pipeline end-to-end : vidéo .mp4 → .glb prêt pour Three.js
    """
    base          = "C:/projet/"
    json_tmp      = f"{base}tmp/{nom_signe}_tmp.json"
    glb_sortie    = f"{base}static/animations/{nom_signe}.glb"
    avatar_blend  = f"{base}avatar_base.blend"
    script_blender= f"{base}json_to_glb.py"
    blender_exe   = "C:/Program Files/Blender Foundation/Blender 4.x/blender.exe"

    # Étape 1 : vidéo → JSON via MediaPipe
    from video_to_pose_json import video_vers_json
    video_vers_json(
        chemin_video     = chemin_video,
        chemin_rest_pose = f"{base}LSF_Bonjour_F1_neutre.json",
        chemin_sortie    = json_tmp
    )

    # Étape 2 : JSON → GLB via Blender headless
    subprocess.run([
        blender_exe,
        "--background",          # pas d'interface graphique
        "--python", script_blender,
        "--",                    # tout ce qui suit est passé au script
        json_tmp,
        avatar_blend,
        glb_sortie
    ])

    # Nettoyage du JSON temporaire
    os.remove(json_tmp)
    print(f"🎉 Pipeline terminé → {glb_sortie}")


# ── Utilisation ────────────────────────────────────────────────────────────────
pipeline_complet("videos_lsf/bonjour.mp4", "LSF_Bonjour")