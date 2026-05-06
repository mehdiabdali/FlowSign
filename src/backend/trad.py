import spacy

# Chargement du modèle linguistique français
nlp = spacy.load("fr_core_news_sm")

def traduire_vers_lsf(texte):
    doc = nlp(texte)
    
    marqueur_temps, sujets, objets, verbes, negations, autres = [], [], [], [], [], []
    temps_global = None

    # --- NOUVEAU : On vérifie d'abord si un marqueur temporel existe dans toute la phrase ---
    mots_cles_temps = [mot.lemma_.upper() for mot in doc]
    a_un_marqueur_explicite = any(m in ["DEMAIN", "HIER", "AVANT-HIER", "APRÈS-DEMAIN"] for m in mots_cles_temps)

    for mot in doc:
        lemme = mot.lemma_.upper()
        nature = mot.pos_
        fonction = mot.dep_

        #utile pour debuguer
        print(f"{mot.text:10} | {lemme:10} | {nature:6} | {fonction} ")  

        # (Blocs 1, 2, 3 identiques...)
        if nature in ["PUNCT", "SPACE", "DET", "ADP", "CCONJ", "SCONJ"] or lemme in ["NE", "N'"]:
            continue
        
        if lemme in ["PAS", "JAMAIS", "RIEN", "PLUS"]:
            if lemme not in negations:
                negations.append(lemme)
            continue

        # 5. Gestion des verbes et du temps
        if nature in ["VERB", "AUX"]:
            if lemme == "ALLER":
                # On n'ajoute le marqueur que si on n'a pas de "DEMAIN"
                if not a_un_marqueur_explicite:
                    temps_global = "(FUTUR)"
                continue
            
            t = mot.morph.get("Tense")
            # On n'ajoute le marqueur automatique QUE si aucun mot comme "DEMAIN" n'est présent
            if t and temps_global is None and not a_un_marqueur_explicite:
                if "Fut" in t: 
                    temps_global = "(FUTUR)"
                elif "Past" in t or "Imp" in t: 
                    temps_global = "(PASSÉ)"
        
        # Identification des marqueurs
        if lemme in ["DEMAIN", "HIER", "AVANT-HIER", "APRÈS-DEMAIN"]:
            nature = "marqueur_temps"

        # 6. Tri syntaxique
        if fonction in ["nsubj", "expl"]:
            if lemme not in sujets: 
                sujets.append(lemme)
        elif fonction in ["obj", "iobj", "nmod"]: 
            objets.append(lemme)
        elif nature in ["VERB", "AUX"]: 
            verbes.append(lemme)
        elif nature == "marqueur_temps":
            marqueur_temps.append(lemme)
        else:
            autres.append(lemme)

    # 7. Assemblage final
    phrase = marqueur_temps + sujets + objets + autres + verbes + negations

    # On n'ajoute le jeton (FUTUR) ou (PASSÉ) que si on n'a pas de marqueur précis
    if temps_global and not marqueur_temps: 
        phrase.append(temps_global)
    
    return phrase