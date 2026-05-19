/*
Auteur : Mehdi ABD ALI
Gère tout ce qui touche à la 3D et à Three.js.
L'interface HTML n'a pas à savoir comment le moteur 3D fonctionne à l'intérieur.
*/

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

let scene, camera, renderer, mixer, avatar;
const loader = new GLTFLoader();
const clock = new THREE.Clock();

// Variables pour la lecture des signes
let sequenceFichiers = []; 
let indexLecture = 0; 
let ecouteurFinAnimation = null; 
let actionPrecedente = null; 
let vitesseActuelle = 1;

// Fonction que l'on va appeler pour le surlignage des mots (karaoké)
let callbackChangementMot = null;

export function initScene(containerId) {
    const container = document.getElementById(containerId);
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf0f0f0);

    const largeur = container.clientWidth || 500;
    const hauteur = container.clientHeight || 480;

    // On prépare la caméra
    camera = new THREE.PerspectiveCamera(45, largeur / hauteur, 0.1, 100);
    camera.position.set(0, 1.5, 5);

    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(largeur, hauteur);
    container.appendChild(renderer.domElement);

    // On ajoute de la lumière pour bien voir les volumes du modèle
    const ambientLight = new THREE.AmbientLight(0xffffff, 2);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(2, 2, 2);
    scene.add(directionalLight);

    // On charge le personnage par défaut
    const urlAvatar = 'static/animations/avatar_base.glb';
    loader.load(urlAvatar, (gltf) => {
        avatar = gltf.scene;
        avatar.position.y = -1;
        scene.add(avatar);
        
        // Le mixer est le chef d'orchestre qui joue les animations
        mixer = new THREE.AnimationMixer(avatar);
        animate();
    }, undefined, (error) => console.error("Erreur de chargement de l'avatar :", error));

    // Pour que la fenêtre 3D s'adapte au redimensionnement de l'écran
    window.addEventListener('resize', () => {
        if (!container) return;
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    });
}

export function definirCallbackMot(callback) {
    callbackChangementMot = callback;
}

export function jouerSequence(fichiers) {
    sequenceFichiers = fichiers;
    indexLecture = 0;
    actionPrecedente = null;
    // On arrête les animations en cours avant d'en lancer de nouvelles
    if (mixer) mixer.stopAllAction();
    appliquerAnimationSequence(0);
}

function appliquerAnimationSequence(index) {
    if (!avatar || !mixer) return;
    
    // Condition d'arrêt : on a tout lu
    if (index >= sequenceFichiers.length) {
        if (callbackChangementMot) callbackChangementMot(-1, sequenceFichiers.length);
        indexLecture = 0;
        actionPrecedente = null; 
        return; 
    }

    indexLecture = index;
    if (callbackChangementMot) callbackChangementMot(index, sequenceFichiers.length);

    const urlFichier3D = '/' + sequenceFichiers[index];

    loader.load(urlFichier3D, (gltf) => {
        const clip = gltf.animations[0];

        if (clip) {
            const action = mixer.clipAction(clip, avatar);
            action.setLoop(THREE.LoopOnce);
            action.clampWhenFinished = true; // Fige le personnage à la fin du mouvement

            // S'il y a déjà une animation, on fait une transition douce
            if (actionPrecedente) {
                action.play();
                actionPrecedente.crossFadeTo(action, 0.2, true);
            } else {
                mixer.stopAllAction();
                action.play();
            }

            actionPrecedente = action;

            // On nettoie l'écouteur précédent pour éviter les déclenchements multiples
            if (ecouteurFinAnimation) {
                mixer.removeEventListener('finished', ecouteurFinAnimation);
            }

            // On enchaîne automatiquement avec le signe suivant
            ecouteurFinAnimation = function() {
                appliquerAnimationSequence(indexLecture + 1);
            };
            
            mixer.addEventListener('finished', ecouteurFinAnimation);
        }
    }, undefined, (error) => console.error("Erreur de chargement de l'animation :", error));
}

export function changerVitesse(vitesse) {
    vitesseActuelle = vitesse;
    if (mixer && mixer.timeScale > 0) mixer.timeScale = vitesseActuelle;
}

export function mettreEnPause() {
    if (mixer) mixer.timeScale = 0;
}

export function reprendreLecture() {
    if (!mixer) return;
    if (mixer.timeScale === 0) {
        mixer.timeScale = vitesseActuelle; 
    } else {
        // Si la phrase est terminée, on relance l'animation en cours
        mixer.timeScale = vitesseActuelle;
        actionPrecedente = null;
        appliquerAnimationSequence(indexLecture);
    }
}

export function relancerDuDebut() {
    if (mixer) {
        mixer.timeScale = vitesseActuelle;
        mixer.stopAllAction();
        actionPrecedente = null;
        appliquerAnimationSequence(0);
    }
}

function animate() {
    requestAnimationFrame(animate);
    // On met à jour le temps en fonction du taux de rafraîchissement (FPS)
    const delta = clock.getDelta();
    if (mixer) mixer.update(delta);
    renderer.render(scene, camera);
}