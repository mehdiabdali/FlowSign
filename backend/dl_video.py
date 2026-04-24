import requests
import re

def telecharger_video_elix(mot, dossier_sortie="/Users/gaspardc/Downloads/"):
    """
    Récupère l'URL de la vidéo pour un mot donné sur Elix.
    """
    url_page = f"https://dico.elix-lsf.fr/dictionnaire/{mot}"
    headers  = {"User-Agent": "Mozilla/5.0"}

    resp = requests.get(url_page, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Page introuvable pour '{mot}' (status {resp.status_code})")
        return None

    # Chercher l'URL de la vidéo dans le HTML
    matches = re.findall(r'https://[^"\']+\.mp4[^"\']*', resp.text)
    if not matches:
        print(f"❌ Aucune vidéo trouvée pour '{mot}'")
        print("   Essaie d'inspecter manuellement la page avec F12")
        return None

    video_url = matches[0]
    print(f"✅ Vidéo trouvée : {video_url[:80]}...")

    # Télécharger
    video_resp = requests.get(video_url, headers=headers, stream=True)
    out_path   = f"{dossier_sortie}/{mot}.mp4"
    with open(out_path, 'wb') as f:
        for chunk in video_resp.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"💾 Vidéo sauvegardée : {out_path}")
    return out_path

telecharger_video_elix("merci")