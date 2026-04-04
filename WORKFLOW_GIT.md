# Workflow Git + Docker — Guide complet

## Schéma du fonctionnement

```
Votre PC (développement)
        ↓  git push
    GitHub (code source)
        ↓  git clone / git pull
PC du client (utilisation)
        ↓  docker-compose up
  Application dans le navigateur
```

---

## PARTIE 1 — Sur votre PC (une seule fois)

### 1. Installer Git
Télécharger : https://git-scm.com/download/win
Installer avec les options par défaut.

### 2. Créer un compte GitHub
Aller sur : https://github.com → Sign up (gratuit)

### 3. Créer un dépôt GitHub
1. Cliquer **New repository**
2. Nom : `pdf-douanes`
3. Visibilité : **Private** (personne ne voit votre code)
4. Cliquer **Create repository**

### 4. Initialiser Git dans votre dossier
Ouvrir CMD dans le dossier `pdf_database` :

```bash
git init
git add .
git commit -m "premier commit"
git branch -M main
git remote add origin https://github.com/VOTRE_NOM/pdf-douanes.git
git push -u origin main
```

✅ Votre code est maintenant sur GitHub.

---

## PARTIE 2 — Chaque fois que vous modifiez le code

```bash
# Voir ce qui a changé
git status

# Ajouter les modifications
git add .

# Sauvegarder avec un message
git commit -m "description de ce que j'ai changé"

# Envoyer sur GitHub
git push
```

---

## PARTIE 3 — Livrer l'application au client

### Sur le PC du client (une seule fois)

**1. Installer Docker Desktop**
→ https://www.docker.com/products/docker-desktop/
→ Installer et lancer Docker Desktop

**2. Installer Git**
→ https://git-scm.com/download/win

**3. Télécharger votre application**
```bash
git clone https://github.com/VOTRE_NOM/pdf-douanes.git
cd pdf-douanes
```

**4. Lancer l'application**
Double-clic sur **`LANCER_DOCKER.bat`**

→ Première fois : 3-5 minutes (télécharge les dépendances)
→ Fois suivantes : 5 secondes

→ Le navigateur s'ouvre sur http://localhost:8501
→ Login : admin@douanes.tn / Admin1234!

---

## PARTIE 4 — Mettre à jour le client

Quand vous faites une mise à jour, le client fait juste :

```bash
# Dans le dossier pdf-douanes
git pull
docker-compose up -d --build
```

Ou double-clic sur **`METTRE_A_JOUR.bat`** (voir ci-dessous).

---

## Commandes Docker utiles

```bash
# Demarrer
docker-compose up -d

# Arreter
docker-compose down

# Voir les logs si probleme
docker-compose logs

# Reconstruire apres modification du code
docker-compose up -d --build

# Voir les containers qui tournent
docker ps
```

---

## Les données du client sont-elles perdues lors d'une mise à jour ?

NON. Le dossier `data/` est un **volume Docker** :
- Les PDFs, la base SQLite et les comptes utilisateurs sont sur le PC du client
- Une mise à jour du code ne touche jamais aux données
- Même si Docker est réinstallé, les données restent dans le dossier `data/`

---

## Résumé visuel

| Action | Commande |
|--------|----------|
| Sauvegarder modification | `git add . && git commit -m "..."` |
| Envoyer sur GitHub | `git push` |
| Récupérer une mise à jour (client) | `git pull` |
| Démarrer l'app (client) | `docker-compose up -d` |
| Arrêter l'app (client) | `docker-compose down` |
