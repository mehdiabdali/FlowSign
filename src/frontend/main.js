/*
Auteur : Mehdi ABD ALI
Script principal qui fait le lien entre l'API, le moteur 3D et le HTML.
C'est le chef d'orchestre de la page web.
*/

import { traduireTexte, recupererDictionnaire } from './api.js';
import { 
    initScene, 
    jouerSequence, 
    changerVitesse, 
    mettreEnPause, 
    reprendreLecture, 
    relancerDuDebut,
    definirCallbackMot
} from './scene.js';

// 1. LIAISON AVEC LE HTML
// On récupère tous les éléments de l'interface
const boutonTraduire = document.getElementById('btnTraduire');
const champTexte = document.getElementById('champTexte');
const zoneResultat = document.getElementById('resultat');

const btnDico = document.getElementById('btnDico');
const zoneDico = document.getElementById('zoneDico');
const conteneurMots = document.getElementById('conteneurMots');
const champRecherche = document.getElementById('rechercheDico');

const selectVitesse = document.getElementById('selectVitesse');
const btnPlay = document.getElementById('btnPlay');
const btnPause = document.getElementById('btnPause');
const btnRestart = document.getElementById('btnRestart');

let motsDictionnaire = [];

// 2. LOGIQUE DE TRADUCTION
async function executerTraduction() {
    // On retire les espaces superflus
    const texte = champTexte.value.trim();
    if (!texte) return;

    zoneResultat.innerHTML = "<em>Analyse en cours...</em>";
    surlignerMot(-1, 0); 
    document.getElementById('controles-lecture').style.display = 'none';
    
    // On fige l'avatar pendant le chargement
    mettreEnPause();

    try {
        const data = await traduireTexte(texte);

        if (data.mots_traduits && data.mots_traduits.length > 0) {
            // On affiche en rouge les mots manquants, en vert ceux traduits
            const motsFormates = data.mots_traduits.map((mot, i) => {
                if (data.mots_sans_animation && data.mots_sans_animation.includes(mot)) {
                    return `<span id="mot-${i}" style="color:red; transition: all 0.3s; padding: 2px 6px; border-radius: 4px; border: 2px solid transparent;" title="Aucune animation disponible">⚠ ${mot}</span>`;
                }
                return `<span id="mot-${i}" style="color:green; transition: all 0.3s; padding: 2px 6px; border-radius: 4px; border: 2px solid transparent;">${mot}</span>`;
            });

            let html = `Séquence LSF : ${motsFormates.join(' → ')}`;

            // Message d'erreur s'il manque des signes dans la base de données
            if (!data.traduction_complete) {
                const listeManquants = data.mots_sans_animation.join(', ');
                html += `<br><br><span style="color:red;">❌ Animation impossible : ${listeManquants}</span>`;
            }
            
            zoneResultat.innerHTML = html;
                
            // On envoie la liste des fichiers à la scène 3D
            if (data.fichiers_glb && data.fichiers_glb.length > 0) {
                jouerSequence(data.fichiers_glb);
                document.getElementById('controles-lecture').style.display = 'flex';
            }
        } else {
            zoneResultat.innerHTML = "<em>Aucun mot LSF extrait de cette phrase.</em>";
        }
    } catch (error) {
        console.error("Erreur API :", error);
        zoneResultat.innerHTML = "<span style='color:red;'>Erreur : impossible de joindre le serveur.</span>";
    }
}

// 3. EFFET KARAOKÉ
function surlignerMot(index, total) {
    // On réinitialise l'affichage des mots
    for (let i = 0; i < total; i++) {
        const elementMot = document.getElementById(`mot-${i}`);
        if (elementMot) {
            elementMot.style.backgroundColor = "transparent";
            elementMot.style.borderColor = "transparent";
        }
    }
    // On surligne uniquement le mot en cours de lecture
    if (index >= 0 && index < total) {
        const motActuel = document.getElementById(`mot-${index}`);
        if (motActuel) {
            motActuel.style.backgroundColor = "#e3f2fd"; 
            motActuel.style.borderColor = "#2196F3"; 
        }
    }
}

// On passe la fonction à scene.js pour qu'elle l'appelle au bon moment
definirCallbackMot(surlignerMot);

// 4. DICTIONNAIRE
function afficherMots(liste) {
    if (liste.length > 0) {
        const htmlMots = liste.map(lemme => {
            return `<span style="display: inline-block; background-color: #e0e0e0; color: #333; padding: 5px 12px; margin: 4px; border-radius: 15px; font-size: 14px;">${lemme.toLowerCase().replace(/_/g, ' ')}</span>`;
        });
        conteneurMots.innerHTML = htmlMots.join('');
    } else {
        conteneurMots.innerHTML = "<em>Aucun signe trouvé.</em>";
    }
}

async function gererDictionnaire() {
    // On affiche ou on cache la zone selon son état actuel
    if (zoneDico.style.display === 'block') {
        zoneDico.style.display = 'none';
        btnDico.textContent = "Voir les mots disponibles";
        return;
    }

    conteneurMots.innerHTML = '<em>Chargement...</em>';
    zoneDico.style.display = 'block';
    btnDico.textContent = "Cacher le dictionnaire";
    champRecherche.value = ""; 

    try {
        const data = await recupererDictionnaire();
        if (data.mots && data.mots.length > 0) {
            motsDictionnaire = data.mots;
            afficherMots(motsDictionnaire);
        } else {
            conteneurMots.innerHTML = "<em>Base vide.</em>";
        }
    } catch (error) {
        conteneurMots.innerHTML = "<span style='color:red;'>Erreur serveur.</span>";
    }
}

// Recherche de mots en temps réel
champRecherche.addEventListener('input', (e) => {
    const texte = e.target.value.toLowerCase();
    afficherMots(motsDictionnaire.filter(l => l.toLowerCase().replace(/_/g, ' ').includes(texte)));
});

// 5. ÉCOUTEURS D'ÉVÉNEMENTS
boutonTraduire.addEventListener('click', executerTraduction);

// Permet de valider la traduction avec la touche Entrée
champTexte.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        executerTraduction();
    }
});

btnDico.addEventListener('click', gererDictionnaire);

if (selectVitesse) {
    selectVitesse.addEventListener('change', (e) => changerVitesse(parseFloat(e.target.value)));
}

btnPlay.addEventListener('click', reprendreLecture);
btnPause.addEventListener('click', mettreEnPause);
btnRestart.addEventListener('click', relancerDuDebut);

// On lance l'initialisation au démarrage de la page
initScene('canvas-3d');