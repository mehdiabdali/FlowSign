/*
Auteur : Mehdi ABD ALI
Gère la communication avec le backend Flask.
Cela évite de tout mélanger et rend le code plus propre.
*/

const API_URL = ""; 

export async function traduireTexte(texte) {
    // On fait la requête à l'API
    const reponse = await fetch(`${API_URL}/api/traduire`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texte: texte })
    });
    // Si la requête échoue, on lève une erreur
    if (!reponse.ok) throw new Error("Erreur serveur API");
    return await reponse.json();
}

export async function recupererDictionnaire() {
    // On récupère la liste des mots disponibles
    const reponse = await fetch(`${API_URL}/api/dictionnaire`);
    if (!reponse.ok) throw new Error("Erreur serveur API");
    return await reponse.json();
}