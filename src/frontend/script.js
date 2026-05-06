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

/* VARIABLES GLOBALES POUR LE LECTEUR ET LA VITESSE */
let sequenceFichiers = [];
let sequenceMots = [];
let indexLecture = 0;
let ecouteurFinAnimation = null;
let vitesseActuelle = 1;
let actionPrecedente = null;

/* INITIALISATION DE LA SCÈNE 3D */
function initScene() {
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf0f0f0);

    const largeur = container.clientWidth || 500;
    const hauteur = container.clientHeight || 480;

    camera = new THREE.PerspectiveCamera(45, largeur / hauteur, 0.1, 100);
    camera.position.set(0, 1.5, 5);

    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(largeur, hauteur);
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

    window.addEventListener('resize', () => {
        if (!container) return;
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    });
}

/* APPLICATION D'UNE ANIMATION EXTERNE (SÉQUENCE AVEC FONDU) */
function appliquerAnimationSequence(index) {
    if (!avatar || !mixer) return;
    
    if (index >= sequenceFichiers.length) {
        mettreAJourIndicateur(-1, sequenceMots.length, "");
        indexLecture = 0;
        actionPrecedente = null; 
        return; 
    }

    indexLecture = index;
    mettreAJourIndicateur(index, sequenceFichiers.length, sequenceMots[index]);

    loader.load(sequenceFichiers[index], (gltf) => {
        const clip = gltf.animations[0];

        if (clip) {
            const action = mixer.clipAction(clip, avatar);
            action.setLoop(THREE.LoopOnce);
            action.clampWhenFinished = true;

            if (actionPrecedente) {
                action.play();
                actionPrecedente.crossFadeTo(action, 0.2, true);
            } else {
                mixer.stopAllAction();
                action.play();
            }

            actionPrecedente = action;

            if (ecouteurFinAnimation) {
                mixer.removeEventListener('finished', ecouteurFinAnimation);
            }

            ecouteurFinAnimation = function() {
                appliquerAnimationSequence(indexLecture + 1);
            };
            
            mixer.addEventListener('finished', ecouteurFinAnimation);
        }
    }, undefined, (error) => console.error("Erreur chargement animation :", error));
}

/* COMMUNICATION AVEC LE BACKEND */
async function executerTraduction() {
    const texte = champTexte.value.trim();
    if (!texte) return;

    zoneResultat.innerHTML = "<em>Analyse en cours...</em>";
    mettreAJourIndicateur(-1, 0, ""); 
    
    document.getElementById('controles-lecture').style.display = 'none';
    
    if (mixer) {
        mixer.stopAllAction();
        mixer.timeScale = vitesseActuelle;
        actionPrecedente = null;
    }

    try {
        const reponse = await fetch('http://127.0.0.1:5000/api/traduire', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ texte: texte })
        });

        if (!reponse.ok) throw new Error("Erreur serveur");

        const data = await reponse.json();

        if (data.mots_traduits && data.mots_traduits.length > 0) {
            const motsFormates = data.mots_traduits.map((mot, i) => {
                if (data.mots_sans_animation && data.mots_sans_animation.includes(mot)) {
                    return `<span id="mot-${i}" style="color:red; transition: all 0.3s; padding: 2px 6px; border-radius: 4px; border: 2px solid transparent;" title="Aucune animation disponible">⚠ ${mot}</span>`;
                }
                return `<span id="mot-${i}" style="color:green; transition: all 0.3s; padding: 2px 6px; border-radius: 4px; border: 2px solid transparent;">${mot}</span>`;
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
                    sequenceFichiers = data.fichiers_glb;
                    sequenceMots = data.mots_traduits.filter(mot => !data.mots_sans_animation.includes(mot));
                    indexLecture = 0;
                    
                    document.getElementById('controles-lecture').style.display = 'flex';
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

/* MISE EN SURBRILLANCE (EFFET KARAOKÉ) */
function mettreAJourIndicateur(index, total, mot) {
    for (let i = 0; i < total; i++) {
        const elementMot = document.getElementById(`mot-${i}`);
        if (elementMot) {
            elementMot.style.backgroundColor = "transparent";
            elementMot.style.borderColor = "transparent";
        }
    }

    if (index >= 0 && index < total) {
        const motActuel = document.getElementById(`mot-${index}`);
        if (motActuel) {
            motActuel.style.backgroundColor = "#e3f2fd"; 
            motActuel.style.borderColor = "#2196F3"; 
        }
    }
}

/* BOUCLE DE RENDU 3D */
function animate() {
    requestAnimationFrame(animate);
    const delta = clock.getDelta();
    if (mixer) mixer.update(delta);
    renderer.render(scene, camera);
}

/* --- SYSTÈME DE DICTIONNAIRE --- */
const btnDico = document.getElementById('btnDico');
const zoneDico = document.getElementById('zoneDico');
const conteneurMots = document.getElementById('conteneurMots');
const champRecherche = document.getElementById('rechercheDico');
let motsDictionnaire = [];

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
            conteneurMots.innerHTML = "<em>Aucun mot n'est encore enregistré.</em>";
        }
    } catch (error) {
        console.error("Erreur dictionnaire :", error);
        conteneurMots.innerHTML = "<span style='color:red;'>Erreur : Impossible de joindre le serveur.</span>";
    }
}

champRecherche.addEventListener('input', (e) => {
    const texteRecherche = e.target.value.toLowerCase();
    const motsFiltres = motsDictionnaire.filter(lemme => {
        const motLisible = lemme.toLowerCase().replace(/_/g, ' ');
        return motLisible.includes(texteRecherche);
    });
    afficherMots(motsFiltres);
});

/* --- TOUS LES ÉCOUTEURS D'ÉVÉNEMENTS --- */
boutonTraduire.addEventListener('click', executerTraduction);

champTexte.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        executerTraduction();
        appliquerAnimationSequence(0);
    }
});

btnDico.addEventListener('click', chargerDictionnaire);

const selectVitesse = document.getElementById('selectVitesse');
if (selectVitesse) {
    selectVitesse.addEventListener('change', (e) => {
        vitesseActuelle = parseFloat(e.target.value);
        if (mixer && mixer.timeScale > 0) {
            mixer.timeScale = vitesseActuelle;
        }
    });
}

document.getElementById('btnPlay').addEventListener('click', () => {
    if (!mixer) return;
    
    if (mixer.timeScale === 0) {
        mixer.timeScale = vitesseActuelle;
    } else if (indexLecture === 0) {
        mixer.timeScale = vitesseActuelle;
        actionPrecedente = null; 
        appliquerAnimationSequence(0);
    }
});

document.getElementById('btnPause').addEventListener('click', () => {
    if (mixer) {
        mixer.timeScale = 0;
    }
});

document.getElementById('btnRestart').addEventListener('click', () => {
    if (mixer) {
        mixer.timeScale = vitesseActuelle;
        mixer.stopAllAction();
        actionPrecedente = null;
        appliquerAnimationSequence(0);
    }
});

initScene();