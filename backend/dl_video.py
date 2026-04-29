import requests
import re
import os
import time

def telecharger_video_elix(mot, dossier_sortie="/Users/gaspardc/Downloads/"):
    url_page = f"https://dico.elix-lsf.fr/dictionnaire/{mot}"
    headers  = {"User-Agent": "Mozilla/5.0"}
    
    resp = requests.get(url_page, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Page introuvable pour '{mot}' (status {resp.status_code})")
        return None

    matches = re.findall(r'https://[^"\']+\.mp4[^"\']*', resp.text)
    if not matches:
        print(f"❌ Aucune vidéo trouvée pour '{mot}'")
        return None

    video_url = matches[0]
    video_resp = requests.get(video_url, headers=headers, stream=True)
    
    out_path = os.path.join(dossier_sortie, f"{mot}.mp4")
    with open(out_path, 'wb') as f:
        for chunk in video_resp.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"💾 {mot}.mp4 ({os.path.getsize(out_path)//1024} Ko)")
    return out_path


def telecharger_depuis_fichier(mots_path, dossier_sortie, delai=1.0):
    """
    Lit mots.txt et télécharge la vidéo de chaque mot.
    delai : secondes d'attente entre chaque requête (évite le rate limiting)
    """
    os.makedirs(dossier_sortie, exist_ok=True)

    with open(mots_path, 'r', encoding='utf-8') as f:
        mots = [ligne.strip() for ligne in f if ligne.strip()]

    print(f"📋 {len(mots)} mots à télécharger\n")

    ok, echecs = [], []

    for i, mot in enumerate(mots, 1):
        # Vérifier si déjà téléchargé
        dest = os.path.join(dossier_sortie, f"{mot}.mp4")
        if os.path.exists(dest):
            print(f"[{i}/{len(mots)}] ⏭  {mot} — déjà présent")
            ok.append(mot)
            continue

        print(f"[{i}/{len(mots)}] ⬇  {mot}...", end=" ", flush=True)
        try:
            result = telecharger_video_elix(mot, dossier_sortie)
            if result:
                ok.append(mot)
            else:
                echecs.append(mot)
        except Exception as e:
            print(f"❌ Erreur : {e}")
            echecs.append(mot)

        # Pause entre les requêtes
        if i < len(mots):
            time.sleep(delai)

    # Résumé
    print(f"\n{'='*40}")
    print(f"✅ Réussis  : {len(ok)}/{len(mots)}")
    print(f"❌ Échecs   : {len(echecs)}")
    if echecs:
        print(f"   Mots manquants : {', '.join(echecs)}")

        # Sauvegarder les échecs pour relancer plus tard
        echecs_path = os.path.join(dossier_sortie, "_echecs.txt")
        with open(echecs_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(echecs))
        print(f"   → Sauvegardé dans {echecs_path}")


# ── Lancement ──────────────────────────────────────────────────────────────────
telecharger_depuis_fichier(
    mots_path      = "./backend/mots.txt",
    dossier_sortie = "./backend/videos_flowsign",
    delai          = 1.5   # secondes entre chaque téléchargement
)