import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

   //1. CONFIGURATION ET VARIABLES D'ENVIRONNEMENT


const API_URL = "http://145.241.174.38:5000"; 

const BUCKET_BASE_URL = "https://objectstorage.eu-paris-1.oraclecloud.com/p/dagBDUq8WL8c1AVz4mXQnYFJ_zHPSut20oLPB1EQBrOvrzyZL6GboXPgCs_Np6x8/n/axkeswuyorub/b/flowsign-frontend/o/";

   //2. RÉCUPÉRATION DES BOUTONS ET ZONES DE TEXTE (HTML)

const container = document.getElementById('canvas-3d');
const boutonTraduire = document.getElementById('btnTraduire');
const champTexte = document.getElementById('champTexte');
const zoneResultat = document.getElementById('resultat');

// Dictionnaire
const btnDico = document.getElementById('btnDico');
const zoneDico = document.getElementById('zoneDico');
const conteneurMots = document.getElementById('conteneurMots');
const champRecherche = document.getElementById('rechercheDico');

// Contrôles de lecture
const selectVitesse = document.getElementById('selectVitesse');
const btnPlay = document.getElementById('btnPlay');
const btnPause = document.getElementById('btnPause');
const btnRestart = document.getElementById('btnRestart');

   //3. VARIABLES D'ÉTAT DE L'APPLICATION

// Moteur 3D
let scene, camera, renderer, mixer, avatar;
const loader = new GLTFLoader();
const clock = new THREE.Clock();

// Gestion de la séquence d'animation LSF
let sequenceFichiers = [];    // Chemins des fichiers renvoyés par l'API
let sequenceMots = [];        // Mots traduits avec succès
let indexLecture = 0;         // Position actuelle dans la phrase
let ecouteurFinAnimation = null; // Référence pour nettoyer les événements
let actionPrecedente = null;  // Permet de gérer la transition fluide (crossfade)
let vitesseActuelle = 1;

// Données
let motsDictionnaire = [];    // Stocke le vocabulaire pour la recherche locale

   //4. INITIALISATION DU MOTEUR 3D (THREE.JS)

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

    // Éclairage standard pour bien voir les volumes du personnage
    const ambientLight = new THREE.AmbientLight(0xffffff, 2);
    scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(2, 2, 2);
    scene.add(directionalLight);

    // Chargement de l'avatar au démarrage du site (directement depuis le Bucket OCI)
    const urlAvatar = BUCKET_BASE_URL + 'static/animations/avatar_base.glb';
    loader.load(urlAvatar, (gltf) => {
        avatar = gltf.scene;
        avatar.position.y = -1;
        scene.add(avatar);
        
        // Le mixer est le chef d'orchestre qui gère la lecture des animations
        mixer = new THREE.AnimationMixer(avatar);
        animate();
    }, undefined, (error) => console.error("Erreur chargement avatar de base depuis OCI :", error));

    // Gestion du redimensionnement de la fenêtre
    window.addEventListener('resize', () => {
        if (!container) return;
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    });
}

   //5. LOGIQUE D'ANIMATION (SÉQUENCE LSF)

function appliquerAnimationSequence(index) {
    if (!avatar || !mixer) return;
    
    // Condition d'arrêt : on a joué tous les mots de la phrase
    if (index >= sequenceFichiers.length) {
        mettreAJourIndicateur(-1, sequenceMots.length, "");
        indexLecture = 0;
        actionPrecedente = null; 
        return; 
    }

    indexLecture = index;
    mettreAJourIndicateur(index, sequenceFichiers.length, sequenceMots[index]);

    // On combine l'URL de base du cloud avec le chemin relatif fourni par la base de données
    const urlFichier3D = BUCKET_BASE_URL + sequenceFichiers[index];

    loader.load(urlFichier3D, (gltf) => {
        const clip = gltf.animations[0];

        if (clip) {
            const action = mixer.clipAction(clip, avatar);
            action.setLoop(THREE.LoopOnce);
            action.clampWhenFinished = true; // Empêche l'avatar de revenir en position T à la fin du mouvement

            // S'il y a déjà une animation en cours, on fait une transition douce (crossfade)
            if (actionPrecedente) {
                action.play();
                actionPrecedente.crossFadeTo(action, 0.2, true);
            } else {
                mixer.stopAllAction();
                action.play();
            }

            actionPrecedente = action;

            // On nettoie l'ancien écouteur pour éviter que les événements ne se déclenchent en double
            if (ecouteurFinAnimation) {
                mixer.removeEventListener('finished', ecouteurFinAnimation);
            }

            // On crée le nouvel écouteur qui lancera le mot suivant à la fin du mouvement actuel
            ecouteurFinAnimation = function() {
                appliquerAnimationSequence(indexLecture + 1);
            };
            
            mixer.addEventListener('finished', ecouteurFinAnimation);
        }
    }, undefined, (error) => console.error("Erreur chargement animation depuis OCI :", error));
}

function animate() {
    requestAnimationFrame(animate);
    const delta = clock.getDelta();
    // Le delta time garantit que l'animation tourne à la même vitesse peu importe les FPS de l'écran
    if (mixer) mixer.update(delta);
    renderer.render(scene, camera);
}

   //6. COMMUNICATION API (BACK-END FLASK)

async function executerTraduction() {
    const texte = champTexte.value.trim();
    if (!texte) return;

    zoneResultat.innerHTML = "<em>Analyse en cours...</em>";
    mettreAJourIndicateur(-1, 0, ""); 
    document.getElementById('controles-lecture').style.display = 'none';
    
    // Réinitialisation du lecteur 3D avant de lancer la nouvelle phrase
    if (mixer) {
        mixer.stopAllAction();
        mixer.timeScale = vitesseActuelle;
        actionPrecedente = null;
    }

    try {
        const reponse = await fetch(`${API_URL}/api/traduire`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ texte: texte })
        });

        if (!reponse.ok) throw new Error("Erreur serveur API");

        const data = await reponse.json();

        // Traitement de l'affichage du résultat
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
            }
            
            zoneResultat.innerHTML = html;
                
            // S'il y a au moins un fichier 3D valide, on prépare la séquence et on affiche le lecteur
            if (data.fichiers_glb && data.fichiers_glb.length > 0) {
                sequenceFichiers = data.fichiers_glb;
                sequenceMots = data.mots_traduits.filter(mot => !data.mots_sans_animation.includes(mot));
                indexLecture = 0;
                document.getElementById('controles-lecture').style.display = 'flex';
            }
            
        } else {
            zoneResultat.innerHTML = "<em>Aucun mot LSF extrait de cette phrase.</em>";
        }

    } catch (error) {
        console.error("Erreur API :", error);
        zoneResultat.innerHTML = "<span style='color:red;'>Erreur : impossible de joindre le serveur Flask. Vérifiez que les conteneurs tournent.</span>";
    }
}

// Effet visuel "Karaoké" pour suivre la progression de la phrase
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

   
//7. GESTION DU DICTIONNAIRE

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
        // Correction ici : appel de la route dictionnaire (avec des backticks pour la template string)
        const reponse = await fetch(`${API_URL}/api/dictionnaire`);
        if (!reponse.ok) throw new Error("Erreur serveur API");
        
        const data = await reponse.json();

        if (data.mots && data.mots.length > 0) {
            motsDictionnaire = data.mots;
            afficherMots(motsDictionnaire);
        } else {
            conteneurMots.innerHTML = "<em>Aucun mot n'est encore enregistré dans la base MongoDB.</em>";
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

   //8. ÉCOUTEURS D'ÉVÉNEMENTS (Events Binding)

boutonTraduire.addEventListener('click', executerTraduction);

champTexte.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        executerTraduction();
    }
});

btnDico.addEventListener('click', chargerDictionnaire);

if (selectVitesse) {
    selectVitesse.addEventListener('change', (e) => {
        vitesseActuelle = parseFloat(e.target.value);
        if (mixer && mixer.timeScale > 0) {
            mixer.timeScale = vitesseActuelle;
        }
    });
}

btnPlay.addEventListener('click', () => {
    if (!mixer) return;
    
    if (mixer.timeScale === 0) {
        mixer.timeScale = vitesseActuelle; // Reprise après pause
    } else if (indexLecture === 0) {
        mixer.timeScale = vitesseActuelle; // Lancement initial
        actionPrecedente = null; 
        appliquerAnimationSequence(0);
    }
});

btnPause.addEventListener('click', () => {
    if (mixer) {
        mixer.timeScale = 0; // Met l'animation en pause
    }
});

btnRestart.addEventListener('click', () => {
    if (mixer) {
        mixer.timeScale = vitesseActuelle;
        mixer.stopAllAction();
        actionPrecedente = null;
        appliquerAnimationSequence(0); // Relance depuis le premier mot
    }
});

// Lancement automatique de la scène au chargement du script
initScene();