import pytest
from trad import traduire_vers_lsf

# ─── Tests de base ───────────────────────────────────────────

def test_phrase_vide():
    assert traduire_vers_lsf("") == []

def test_espaces_seulement():
    assert traduire_vers_lsf("   ") == []

def test_mot_simple():
    resultat = traduire_vers_lsf("manger")
    assert "MANGER" in resultat

def test_sujet_verbe():
    resultat = traduire_vers_lsf("je mange")
    assert resultat.index("JE") < resultat.index("MANGER")

def test_sujet_objet_verbe():
    resultat = traduire_vers_lsf("je mange une pomme")
    assert "JE" in resultat
    assert "POMME" in resultat
    assert "MANGER" in resultat
    # En LSF le verbe est après l'objet
    assert resultat.index("POMME") < resultat.index("MANGER")

# ─── Tests pronoms ───────────────────────────────────────────

def test_pronom_moi():
    resultat = traduire_vers_lsf("moi je mange")
    assert "JE" in resultat

def test_pronom_toi():
    resultat = traduire_vers_lsf("toi tu pars")
    assert "TU" in resultat

def test_pronom_lui():
    resultat = traduire_vers_lsf("lui il court")
    assert "IL" in resultat

# ─── Tests temps ─────────────────────────────────────────────

def test_temps_futur_marqueur():
    resultat = traduire_vers_lsf("demain je pars")
    assert "(FUTUR)" in resultat
    assert resultat.index("(FUTUR)") == 0  # toujours en premier

def test_temps_passe_marqueur():
    resultat = traduire_vers_lsf("hier je suis parti")
    assert "(PASSÉ)" in resultat
    assert resultat.index("(PASSÉ)") == 0

def test_futur_proche():
    resultat = traduire_vers_lsf("je vais manger")
    assert "(FUTUR)" in resultat

def test_demain_pas_dans_phrase():
    """DEMAIN ne doit pas apparaître comme mot dans la phrase LSF"""
    resultat = traduire_vers_lsf("demain je pars")
    assert "DEMAIN" not in resultat

def test_hier_pas_dans_phrase():
    resultat = traduire_vers_lsf("hier je suis parti")
    assert "HIER" not in resultat

# ─── Tests négation ──────────────────────────────────────────

def test_negation_pas():
    resultat = traduire_vers_lsf("je n'aime pas le chat")
    assert "PAS" in resultat
    # La négation est toujours à la fin en LSF
    assert resultat.index("PAS") == len(resultat) - 1

def test_negation_jamais():
    resultat = traduire_vers_lsf("je ne mange jamais")
    assert "JAMAIS" in resultat
    assert resultat.index("JAMAIS") == len(resultat) - 1

# ─── Tests filtrage ──────────────────────────────────────────

def test_filtrage_determinants():
    """Les déterminants ne doivent pas apparaître"""
    resultat = traduire_vers_lsf("le chat mange la souris")
    assert "LE" not in resultat
    assert "LA" not in resultat
    assert "UN" not in resultat

def test_filtrage_conjonctions():
    """Les conjonctions ne doivent pas apparaître"""
    resultat = traduire_vers_lsf("je mange et je bois")
    assert "ET" not in resultat

def test_filtrage_ne():
    """Le 'ne' de négation ne doit pas apparaître"""
    resultat = traduire_vers_lsf("je ne mange pas")
    assert "NE" not in resultat
    assert "N'" not in resultat