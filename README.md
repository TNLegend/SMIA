# SMIA Platform

SMIA ("Système de Management de l'IA") est une plateforme web permettant la gestion de projets d'intelligence artificielle tout en suivant la norme ISO&nbsp;42001. Elle fournit un backend FastAPI et un frontend React afin de centraliser la création de projets, le suivi des tâches ISO, l'échange de documents et l'exécution d'outils de machine learning.

## Prérequis

* **Python 3.11**
* **Node.js ≥ 18** pour le frontend
* Un système Unix (Linux/macOS) ou WSL sous Windows

## Installation

1. Clonez ce dépôt :
   ```bash
   git clone <repo-url>
   cd SMIA
   ```
2. Créez un environnement virtuel Python et installez les dépendances backend :
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt -r backend/requirements-ml.txt
   ```
3. Installez les dépendances frontend :
   ```bash
   cd frontend
   npm install
   cd ..
   ```

## Configuration

Le backend s'appuie sur un fichier `.env` présent dans `backend/`. Vous pouvez le copier puis l'adapter à votre environnement :

```bash
cp backend/.env backend/.env.local
```

Les variables importantes sont :

- `DATABASE_URL` : URL SQLModel/SQLAlchemy de la base (par défaut SQLite `smia.db`).
- `JWT_SECRET` et `ALGORITHM` : paramètres de génération des jetons.

Pour le frontend, vous pouvez créer un fichier `frontend/.env` pour spécifier l'URL du backend (par défaut `http://127.0.0.1:8000`) :

```
VITE_API_URL=http://127.0.0.1:8000
```

## Lancement du backend

Dans un terminal :

```bash
cd backend
uvicorn app.main:app --reload
```

L'API FastAPI est alors disponible sur <http://127.0.0.1:8000>. Elle expose des routes d'authentification et de gestion des projets, équipes et documents.

## Lancement du frontend

Dans un autre terminal :

```bash
cd frontend
npm run dev
```

L'application React est accessible sur <http://localhost:5173> (port généré par Vite). Le frontend consomme l'API configurée via `VITE_API_URL`.

## Fonctionnalités principales

- Gestion des utilisateurs, des équipes et des projets d'IA
- Checklist ISO&nbsp;42001 pour vérifier la conformité des projets
- Stockage de documents et génération de rapports PDF
- Exécution de tâches Machine Learning (audit, expérimentations)

## Développement

- **Backend** : code Python sous `backend/app`. Le point d'entrée est `main.py` qui déclare les routes FastAPI et initialise la base de données.
- **Frontend** : code TypeScript/React sous `frontend/src`.

Des scripts de nettoyage et de planification se trouvent dans `backend/app/tasks`. Les dépendances liées au machine learning sont listées dans `backend/requirements-ml.txt`.

## Déploiement

Ce dépôt inclut un `Dockerfile.smia-runtime` pour préparer une image Python contenant les bibliothèques Machine Learning nécessaires. Il est possible d'utiliser cet environnement pour exécuter le backend en production.

## Licence

Ce projet est publié sans indication de licence expresse. Les contributions et usages doivent donc être dûment autorisés par le propriétaire du dépôt.

