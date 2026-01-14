# Agenda Chatbot (Gemini)

Chatbot FastAPI avec moteur Gemini + API lagenda.bj pour la recherche d'événements culturels au Bénin.

## Fonctionnalités
- Discussions conversationnelles avec Gemini AI
- Recherche d'événements via l'API lagenda.bj (avec cache en mémoire)
- Interface web moderne et responsive
- Sécurité : validation d'entrée, rate limiting, clés API sécurisées

## Installation

1. Cloner le repo :
   ```bash
   git clone <url_du_repo>
   cd <nom_du_projet>
   ```

2. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

3. Configurer les variables d'environnement :
   - Définir `GEMINI_API_KEY` (obtenir sur Google AI Studio)
   - Optionnel : ajuster `LAGENDA_API_URL` si changé

4. Lancer le serveur :
   ```bash
   uvicorn main:app --reload
   ```

5. Ouvrir http://localhost:8000 dans le navigateur.

## Configuration

- **Clé API Gemini** : Doit être définie comme variable d'environnement (ne pas la mettre dans .env pour la production).
- **Rate Limiting** : 10 requêtes/minute par IP.
- **Cache** : Événements mis en cache pendant 10 minutes.
- **Logging** : Logs structurés pour le débogage.

## Déploiement

- Utiliser un serveur ASGI comme Uvicorn ou Gunicorn.
- Pour production, utiliser des variables d'environnement et un reverse proxy (ex. : Nginx).
- Hébergement possible sur Vercel, Heroku, ou serveur dédié.

## Sécurité

- Clés API non commitées.
- Validation des entrées utilisateur.
- Protection contre les abus (rate limiting).
- Logging pour surveillance.

## Tests

- Tester les endpoints avec Postman ou curl.
- Vérifier la recherche d'événements et les réponses IA.
