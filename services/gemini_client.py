import google.generativeai as genai
import os
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(override=True)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Utilisation du modèle flash pour la rapidité
model = genai.GenerativeModel("gemini-2.5-flash")

async def chat_with_gemini(message: str, history: list = None):
    now = datetime.now()
    # Contexte temporel dynamique : indispensable pour "demain", "ce week-end", etc.
    date_context = f"Aujourd'hui nous sommes le {now.strftime('%A %d %B %Y')}. Heure actuelle : {now.strftime('%H:%M')}."
    
    system_prompt = f"""
         Tu es l'intelligence artificielle de l'Agenda.bj au Bénin. {date_context}
         
         TON RÔLE :
         Convertir les demandes de l'utilisateur en filtres techniques de dates.
         
         RÈGLES D'EXTRACTION TEMPORELLE :
         1. 'date_start' et 'date_end' doivent TOUJOURS être au format YYYY-MM-DD.
         2. SI l'utilisateur dit "aujourd'hui" ou "ce jour" : start et end = date du jour.
         3. SI "ce week-end" : du Vendredi de cette semaine au Dimanche de cette semaine.
         4. SI "le week-end prochain" : du Vendredi au Dimanche de la SEMAINE SUIVANTE.
         5. SI "mois prochain" : du 1er au dernier jour du mois suivant.
         6. SI "en [Mois]" (ex: en Mars) : du 01 au 31 de ce mois en {now.year}.
         7. SI aucune date n'est mentionnée : mets la date d'aujourd'hui dans 'date_start' et laisse 'date_end' à null (pour voir tout le futur).
         8. 'search_query' : extrait uniquement le thème (ex: "concert", "sport", "festival"). Si c'est une question générale ("quoi de neuf"), mets null.
         
         RÉPONDS UNIQUEMENT EN JSON :
         {{
           "intent": "search" | "chat",
           "filters": {{
             "city": string | null,
             "date_start": "YYYY-MM-DD" | null,
             "date_end": "YYYY-MM-DD" | null,
             "search_query": string | null
           }},
           "ai_reply": "Message court et chaleureux (ex: Je cherche les événements pour ce week-end...)"
         }}
         """
    
    # On intègre l'historique pour la continuité
    full_prompt = f"{system_prompt}\n\nHistorique récent: {history}\nUtilisateur: {message}"
    
    try:
        response = await model.generate_content_async(
            full_prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.1 # Rigueur maximale sur le format JSON
            }
        )
        
        # Parsing du JSON renvoyé par Gemini
        return json.loads(response.text)
        
    except Exception as e:
        logging.error(f"Erreur Gemini: {e}")
        return {
            "intent": "chat",
            "filters": {},
            "ai_reply": "Je suis prêt à vous aider ! Que cherchez-vous au Bénin ?"
        }