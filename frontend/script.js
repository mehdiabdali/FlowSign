import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

/* CONFIGURATION ET VARIABLES GLOBALES */
const container = document.getElementById('canvas-3d');
const boutonTraduire = document.getElementById('btnTraduire');
const champTexte = document.getElementById('champTexte');
const zoneResultat = document.getElementById('resultat');

const loader = new GLTFLoader();
const clock = new THREE.Clock();

let scene, camera, renderer, mixer, avatar;

/* INITIALISATION DE LA SCÈNE ET DE L'AVATAR FIXE */
function initScene() {
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf0f0f0);

    camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
    camera.position.set(0, 1.5, 5);

    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);

    const ambientLight = new THREE.AmbientLight(0xffffff, 2);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(2, 2, 2);
    scene.add(directionalLight);

    loader.load('static/animations/avatar_base.glb', (gltf) => {
        avatar = gltf.scene;
        avatar.position.y = -1;
        scene.add(avatar);
        
        mixer = new THREE.AnimationMixer(avatar);
        animate();
    }, undefined, (error) => console.error("Erreur chargement avatar de base :", error));
}

/* APPLICATION D'UNE ANIMATION EXTERNE */
function appliquerAnimationSequence(fichiers, index = 0) {
    if (!avatar || !mixer) return;
    if (index >= fichiers.length) return; // fin de la séquence

    loader.load(fichiers[index], (gltf) => {
        const clip = gltf.animations[0];

        if (clip) {
            mixer.stopAllAction();

            const action = mixer.clipAction(clip, avatar);
            action.setLoop(THREE.LoopOnce);
            action.clampWhenFinished = true;
            action.play();

            // Quand l'animation est terminée → passe à la suivante
            mixer.addEventListener('finished', function passerSuivant() {
                mixer.removeEventListener('finished', passerSuivant); // évite les doublons
                appliquerAnimationSequence(fichiers, index + 1); // signe suivant
            });
        }
    }, undefined, (error) => console.error("Erreur chargement animation :", error));
}

/* LOGIQUE DE COMMUNICATION AVEC LE BACKEND ET GESTION DES ERREURS */
async function executerTraduction() {
    const texte = champTexte.value.trim();
    if (!texte) return;

    zoneResultat.innerHTML = "<em>Analyse en cours...</em>";

    try {
        const reponse = await fetch('http://127.0.0.1:5000/api/traduire', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ texte: texte })
        });

        if (!reponse.ok) throw new Error("Erreur serveur");

        const data = await reponse.json();

        if (data.mots_traduits && data.mots_traduits.length > 0) {
            const motsFormates = data.mots_traduits.map(mot => {
                if (data.mots_sans_animation && data.mots_sans_animation.includes(mot)) {
                    return `<span style="color:red;" title="Aucune animation disponible">⚠ ${mot}</span>`;
                }
                return `<span style="color:green;">${mot}</span>`;
            });

            let html = `Séquence LSF : ${motsFormates.join(' → ')}`;

            if (!data.traduction_complete) {
                const listeManquants = data.mots_sans_animation.join(', ');
                html += `<br><br><span style="color:red;">
                    ❌ Animation impossible : les signes suivants ne sont pas encore dans la base : 
                    ${listeManquants}
                </span>`;
                zoneResultat.innerHTML = html;
            } else {
                zoneResultat.innerHTML = html;
                
                if (data.fichiers_glb && data.fichiers_glb.length > 0) {
                    appliquerAnimationSequence(data.fichiers_glb);
                }
            }
        } else {
            zoneResultat.innerHTML = "<em>Aucun mot LSF extrait de cette phrase.</em>";
        }

    } catch (error) {
        console.error("Erreur API :", error);
        zoneResultat.innerHTML = "<span style='color:red;'>Erreur : impossible de joindre le serveur Flask.</span>";
    }
}

/* BOUCLE DE RENDU (ANIMATION FRAME) */
function animate() {
    requestAnimationFrame(animate);
    const delta = clock.getDelta();
    if (mixer) mixer.update(delta);
    renderer.render(scene, camera);
}

/* ÉCOUTEURS D'ÉVÉNEMENTS */
boutonTraduire.addEventListener('click', executerTraduction);

champTexte.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        executerTraduction();
    }
});

initScene();


/* --- NOUVEAU SYSTÈME DE DICTIONNAIRE AVEC RECHERCHE --- */

const btnDico = document.getElementById('btnDico');
const zoneDico = document.getElementById('zoneDico');
const conteneurMots = document.getElementById('conteneurMots');
const champRecherche = document.getElementById('rechercheDico');

let motsDictionnaire = [];

// Fonction pour afficher les étiquettes HTML
function afficherMots(listeDeMots) {
    if (listeDeMots.length > 0) {
        const htmlMots = listeDeMots.map(lemme => {
            const motLisible = lemme.toLowerCase().replace(/_/g, ' ');
            return `<span style="display: inline-block; background-color: #e0e0e0; color: #333; padding: 5px 12px; margin: 4px; border-radius: 15px; font-size: 14px;">
                ${motLisible}
            </span>`;
        });
        conteneurMots.innerHTML = htmlMots.join('');
    } else {
        conteneurMots.innerHTML = "<em>Aucun signe trouvé pour cette recherche.</em>";
    }
}

async function chargerDictionnaire() {
    if (zoneDico.style.display === 'block') {
        zoneDico.style.display = 'none';
        btnDico.textContent = "Voir les mots disponibles";
        return;
    }

    conteneurMots.innerHTML = '<em>Chargement du dictionnaire...</em>';
    zoneDico.style.display = 'block';
    btnDico.textContent = "Cacher le dictionnaire";
    champRecherche.value = ""; 

    try {
        const reponse = await fetch('http://127.0.0.1:5000/api/dictionnaire');
        
        if (!reponse.ok) throw new Error("Erreur serveur");
        
        const data = await reponse.json();

        if (data.mots && data.mots.length > 0) {
            motsDictionnaire = data.mots;
            afficherMots(motsDictionnaire);
        } else {
            conteneurMots.innerHTML = "<em>Aucun mot n'est encore enregistré dans la base de données.</em>";
        }
    } catch (error) {
        console.error("Erreur dictionnaire :", error);
        conteneurMots.innerHTML = "<span style='color:red;'>Erreur : Impossible de joindre le serveur.</span>";
    }
}

// Filtre de recherche en temps réel
champRecherche.addEventListener('input', (e) => {
    const texteRecherche = e.target.value.toLowerCase();
    
    const motsFiltres = motsDictionnaire.filter(lemme => {
        const motLisible = lemme.toLowerCase().replace(/_/g, ' ');
        return motLisible.includes(texteRecherche);
    });
    
    afficherMots(motsFiltres);
});

btnDico.addEventListener('click', chargerDictionnaire);