#GEMINI.PY
import google.generativeai as genai
import os
import json
import logging
import locale
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(override=True)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Configuration locale française pour les dates
try:
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'French_France.1252')  # Windows
    except:
        pass  # Fallback si locale non disponible

# Utilisation du modèle flash pour la rapidité
model = genai.GenerativeModel("gemini-2.5-flash")

# Catégories d'événements reconnues
CATEGORIES = [
    "concert", "musique", "festival", "spectacle", "théâtre", "danse",
    "sport", "football", "basketball", "marathon", "compétition",
    "conférence", "séminaire", "formation", "atelier", "workshop",
    "exposition", "art", "culture", "cinéma", "film",
    "soirée", "fête", "club", "afterwork", "networking",
    "gastronomie", "cuisine", "dégustation", "marché",
    "enfants", "famille", "jeunesse", "éducation",
    "business", "entrepreneuriat", "startup", "tech",
    "religion", "spiritualité", "cérémonie",
    "mode", "beauté", "lifestyle", "bien-être", "yoga", "fitness"
]

async def chat_with_gemini(message: str, history: list = None):
    now = datetime.now()
    # Contexte temporel dynamique : indispensable pour "demain", "ce week-end", etc.
    date_context = f"Aujourd'hui nous sommes le {now.strftime('%A %d %B %Y')}. Heure actuelle : {now.strftime('%H:%M')}."
    
    # Calcul des dates utiles pour le prompt
    tomorrow = now + timedelta(days=1)
    next_week_start = now + timedelta(days=(7 - now.weekday()))
    
    system_prompt = f"""
         Tu es l'intelligence artificielle de l'Agenda.bj au Bénin. {date_context}
         
         TON RÔLE :
         Analyser la demande de l'utilisateur et extraire TOUS les critères de recherche pertinents.
         
         RÈGLES D'EXTRACTION TEMPORELLE :
         1. 'date_start' et 'date_end' doivent TOUJOURS être au format YYYY-MM-DD.
         2. SI "aujourd'hui" ou "ce jour" ou "ce soir" : start et end = {now.strftime('%Y-%m-%d')}.
         3. SI "demain" : start et end = {tomorrow.strftime('%Y-%m-%d')}.
         4. SI "ce week-end" : du Vendredi au Dimanche de CETTE semaine.
         5. SI "le week-end prochain" ou "prochain week-end" : du Vendredi au Dimanche de la SEMAINE SUIVANTE.
         6. SI "la semaine prochaine" : du Lundi au Dimanche de la semaine suivante.
         7. SI "ce mois" ou "ce mois-ci" : du 1er au dernier jour du mois actuel ({now.year}-{now.month:02d}).
         8. SI "mois prochain" : du 1er au dernier jour du mois suivant.
         9. SI "en [Mois]" (ex: en Mars) : du 01 au dernier jour de ce mois en {now.year}.
         10. SI "en [Année]" (ex: en 2026) : du 01/01 au 31/12 de cette année.
         11. SI aucune date mentionnée : date_start = {now.strftime('%Y-%m-%d')}, date_end = null (événements futurs).
         
         RÈGLES D'EXTRACTION DE CATÉGORIE :
         Catégories reconnues : {', '.join(CATEGORIES[:20])}...
         - Extrais la catégorie principale si mentionnée (ex: "concert", "festival", "sport")
         - Si plusieurs catégories possibles, prends la plus spécifique
         - Si aucune catégorie claire, mets null
         
         RÈGLES D'EXTRACTION DE VILLE :
         Communes et villes du Bénin (77 communes) :
         - LITTORAL : Cotonou
         - ATLANTIQUE : Abomey-Calavi, Allada, Kpomassè, Ouidah, Pahou, Sô-Ava, Toffo, Tori-Bossito, Zè
         - OUÉMÉ : Porto-Novo, Adjarra, Adjohoun, Aguégués, Akpro-Missérété, Avrankou, Bonou, Dangbo, Sèmè-Kpodji
         - PLATEAU : Adja-Ouèrè, Ifangni, Kétou, Pobè, Sakété
         - MONO : Athiémé, Bopa, Comè, Grand-Popo, Houéyogbé, Lokossa
         - COUFFO : Aplahoué, Djakotomey, Dogbo, Klouékanmè, Lalo, Toviklin
         - ZOU : Abomey, Agbangnizoun, Bohicon, Covè, Djidja, Ouinhi, Zagnanado, Za-Kpota, Zogbodomey
         - COLLINES : Bantè, Dassa-Zoumé, Glazoué, Ouèssè, Savalou, Savè
         - BORGOU : Bembèrèkè, Kalalé, N'Dali, Nikki, Parakou, Pèrèrè, Sinendé, Tchaourou
         - ALIBORI : Banikoara, Gogounou, Kandi, Karimama, Malanville, Ségbana
         - ATACORA : Boukoumbé, Cobly, Kérou, Kouandé, Matéri, Natitingou, Péhunco, Tanguiéta, Toucountouna
         - DONGA : Bassila, Copargo, Djougou, Ouaké
         - Extrais la ville/commune si mentionnée
         - Gère les variantes (ex: "Calavi" = "Abomey-Calavi", "PK" = "Porto-Novo")
         
         RÈGLES POUR search_query :
         - Extrais les mots-clés thématiques spécifiques (ex: "jazz", "afrobeat", "startup", "yoga")
         - NE PAS inclure les mots génériques comme "événement", "activité", "truc"
         - Si question générale ("quoi de neuf", "que faire"), mets null
         
         RÈGLES POUR is_free :
         - Si l'utilisateur mentionne "gratuit", "free", "entrée libre" : is_free = true
         - Si l'utilisateur mentionne "payant" : is_free = false
         - Sinon : is_free = null
         
         RÉPONDS UNIQUEMENT EN JSON VALIDE :
         {{
           "intent": "search" | "chat",
           "filters": {{
             "city": string | null,
             "date_start": "YYYY-MM-DD" | null,
             "date_end": "YYYY-MM-DD" | null,
             "category": string | null,
             "search_query": string | null,
             "is_free": boolean | null
           }},
           "ai_reply": "Message court et chaleureux en français (ex: Je cherche les concerts gratuits à Cotonou ce week-end...)"
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