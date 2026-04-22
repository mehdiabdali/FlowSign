import spacy

# Chargement du modèle linguistique français
nlp = spacy.load("fr_core_news_sm")

def traduire_vers_lsf(texte):
    doc = nlp(texte)
    
    sujets, objets, verbes, negations, autres = [], [], [], [], []
    temps_global = None
    verbes_support = ["ALLER", "VENIR"]

    for mot in doc:
        if mot.text.upper() == "MOI":
            lemme = "JE"
            nature = "subj" # On lui donne une vraie nature pour qu'il passe tes filtres
            fonction = "ROOT"
        else:
            # S'exécute uniquement si ce n'est pas ton mot de test
            lemme = mot.lemma_.upper()
            nature = mot.pos_
            fonction = mot.dep_

        # Filtrage
        if nature not in ["PUNCT", "SPACE", "DET", "ADP", "AUX"] and lemme not in ["NE", "N'"]:
            
            if lemme in ["PAS", "JAMAIS", "RIEN", "PLUS"]:
                negations.append(lemme)
            elif lemme in verbes_support and fonction == "xcomp":
                continue
            else:
                # Analyse du temps
                if nature in ["VERB", "AUX"]:
                    t = mot.morph.get("Tense")
                    if t and temps_global is None:
                        if "Fut" in t: temps_global = "FUTUR"
                        elif "Past" in t or "Imp" in t: temps_global = "PASSÉ"
                
                if lemme == "DEMAIN": temps_global = "FUTUR"
                if lemme == "HIER": temps_global = "PASSÉ"

                # Tri syntaxique
                if fonction == "nsubj": sujets.append(lemme)
                elif fonction in ["obj", "iobj", "nmod"]: objets.append(lemme)
                elif nature == "VERB": verbes.append(lemme)
                else:
                    if lemme not in ["DEMAIN", "HIER"]: autres.append(lemme)

    phrase = []
    if temps_global: phrase.append(temps_global)
    phrase += sujets + objets + autres + verbes + negations
    
    return phrase