# json_to_glb.py  —  à lancer DANS Blender (Text Editor) ou en CLI
import bpy
import json
import sys
import mathutils

def json_sequence_vers_glb(chemin_json, chemin_avatar_base, chemin_sortie, fps=24):
    """
    Charge une séquence de poses JSON (produite par video_vers_json.py)
    et génère un fichier .glb avec l'animation intégrée.
    """

    # 1. Charger l'avatar de base (sans animation)
    bpy.ops.wm.open_mainfile(filepath=chemin_avatar_base)

    armature = None
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            armature = obj
            break

    if not armature:
        print("❌ Aucune armature trouvée dans le fichier de base")
        return

    bpy.context.view_layer.objects.active = armature

    # 2. Charger la séquence JSON
    with open(chemin_json, 'r') as f:
        sequence = json.load(f)

    print(f"📂 {len(sequence)} frames chargées")

    # 3. Créer une nouvelle action
    nom_animation = chemin_sortie.split("/")[-1].replace(".glb", "")
    action = bpy.data.actions.new(name=nom_animation)
    armature.animation_data_create()
    armature.animation_data.action = action

    bpy.context.scene.render.fps = fps
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = len(sequence)

    # 4. Appliquer chaque frame et insérer les keyframes
    bpy.ops.object.mode_set(mode='POSE')

    for frame_idx, pose_data in enumerate(sequence):
        frame_num = frame_idx + 1
        bpy.context.scene.frame_set(frame_num)

        for bone in armature.pose.bones:
            if bone.name not in pose_data:
                continue

            q_data = pose_data[bone.name]
            if not all(k in q_data for k in ("w", "x", "y", "z")):
                continue

            bone.rotation_mode = 'QUATERNION'
            bone.rotation_quaternion = mathutils.Quaternion((
                q_data["w"], q_data["x"],
                q_data["y"], q_data["z"]
            ))
            # Insérer la keyframe sur ce bone
            bone.keyframe_insert(data_path="rotation_quaternion", frame=frame_num)

        if frame_idx % 10 == 0:
            print(f"  frame {frame_num}/{len(sequence)}...")

    bpy.ops.object.mode_set(mode='OBJECT')

    # 5. Pousser l'action dans le NLA pour l'export
    bpy.ops.object.select_all(action='DESELECT')
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.nla.bake(
        frame_start=1,
        frame_end=len(sequence),
        only_selected=False,
        visual_keying=True,
        clear_constraints=False,
        use_current_action=True
    )

    # 6. Export GLB
    bpy.ops.export_scene.gltf(
        filepath=chemin_sortie,
        export_format='GLB',
        export_animations=True,
        export_nla_strips=True,
        export_skins=True,
        export_morph=True,
        use_selection=False
    )

    print(f"✅ GLB exporté → {chemin_sortie}")


# ── Utilisation dans Blender Text Editor ──────────────────────────────────────
json_sequence_vers_glb(
    chemin_json        = "C:/projet/animations/LSF_Bonjour_mediapipe.json",
    chemin_avatar_base = "C:/projet/avatar_base.blend",
    chemin_sortie      = "C:/projet/static/animations/LSF_Bonjour.glb",
    fps                = 24
)