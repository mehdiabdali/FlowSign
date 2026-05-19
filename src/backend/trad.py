"""
auteur: Mehdi ABD ALI
Moteur linguistique de l'application. Utilise la librairie spaCy pour analyser 
une phrase en français et la restructurer selon la grammaire LSF.
"""

import spacy

# Chargement du modèle linguistique français (nécessite d'avoir fait python -m spacy download fr_core_news_sm)
nlp = spacy.load("fr_core_news_sm")

def traduire_vers_lsf(texte):
    doc = nlp(texte)
    
    # La LSF possède une structure précise (Temps, Lieu, Sujet, Objet, Action)
    marqueur_temps, sujets, objets, verbes, negations, autres = [], [], [], [], [], []
    temps_global = None

    # On vérifie si un marqueur temporel explicite est déjà présent dans la phrase
    mots_cles_temps = [mot.lemma_.upper() for mot in doc]
    a_un_marqueur_explicite = any(m in ["DEMAIN", "HIER", "AVANT-HIER", "APRÈS-DEMAIN"] for m in mots_cles_temps)

    for mot in doc:
        lemme = mot.lemma_.upper()
        nature = mot.pos_
        fonction = mot.dep_

        # Ligne de débuggage très pratique pour vérifier l'analyse de spaCy
        print(f"{mot.text:10} | {lemme:10} | {nature:6} | {fonction} ")  

        # On supprime les mots inutiles en LSF (déterminants, prépositions, etc.)
        if nature in ["PUNCT", "SPACE", "DET", "ADP", "CCONJ", "SCONJ"] or lemme in ["NE", "N'"]:
            continue
        
        # Isolation des mots de négation
        if lemme in ["PAS", "JAMAIS", "RIEN", "PLUS"]:
            if lemme not in negations:
                negations.append(lemme)
            continue

        # Gestion spécifique des verbes et de la conjugaison temporelle
        if nature in ["VERB", "AUX"]:
            if lemme == "ALLER":
                if not a_un_marqueur_explicite:
                    temps_global = "(FUTUR)"
                continue
            
            t = mot.morph.get("Tense")
            # On déduit le temps global du verbe uniquement si aucun mot temporel n'a été dit
            if t and temps_global is None and not a_un_marqueur_explicite:
                if "Fut" in t: 
                    temps_global = "(FUTUR)"
                elif "Past" in t or "Imp" in t: 
                    temps_global = "(PASSÉ)"
        
        # Catégorisation syntaxique pour la réorganisation finale
        if lemme in ["DEMAIN", "HIER", "AVANT-HIER", "APRÈS-DEMAIN"]:
            nature = "marqueur_temps"

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

    # Assemblage de la phrase selon la syntaxe LSF : Temps -> Sujet -> Objet -> Verbe -> Négation
    phrase = marqueur_temps + sujets + objets + autres + verbes + negations

    if temps_global and not marqueur_temps: 
        phrase.append(temps_global)
    
    return phrase