
#MAIN.PY
import logging
import os
from pathlib import Path
from fastapi import FastAPI, Request # Importation de Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Imports SlowAPI pour le Rate Limit
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

# Vos services optimisés
from services.gemini_client import chat_with_gemini
from services.tools import search_events
from services.filters import filter_events
from services.formatter import format_events

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialisation du Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Configuration des templates
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

class ChatRequest(BaseModel):
    message: str
    history: list = [] 

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

# --- FONCTION CHAT CORRIGÉE ---
@app.post("/chat/")
@limiter.limit("10/minute")
async def chat(request: Request, req: ChatRequest): # 'request' ajouté ici pour SlowAPI
    try:
        # 1. ANALYSE IA
        ai_data = await chat_with_gemini(req.message, req.history)
        
        reply = ai_data.get("ai_reply", "Je traite votre demande...")
        intent = ai_data.get("intent")
        filters = ai_data.get("filters", {})
        
        # Log des filtres extraits pour debug
        logger.info(f"Filtres extraits: {filters}")

        # 2. LOGIQUE DE RECHERCHE
        if intent == "search":
            all_events = await search_events()
            search_filters = filters if filters else {}
            filtered = filter_events(all_events, search_filters)
            
            # Log du nombre de résultats
            logger.info(f"Événements trouvés: {len(filtered)} sur {len(all_events)}")

            if not filtered:
                # Message contextuel selon les filtres utilisés
                context_parts = []
                if search_filters.get('city'):
                    context_parts.append(f"à **{search_filters['city']}**")
                if search_filters.get('category'):
                    context_parts.append(f"dans la catégorie **{search_filters['category']}**")
                if search_filters.get('search_query'):
                    context_parts.append(f"pour **{search_filters['search_query']}**")
                if search_filters.get('is_free'):
                    context_parts.append("**gratuits**")
                
                context_str = " ".join(context_parts) if context_parts else "correspondant à vos critères"
                reply = f"{reply}\n\n📍 *Note :* Je n'ai trouvé aucun événement {context_str}. Essayez d'élargir votre recherche !"
            else:
                # --- LOGIQUE DE LIMITE DYNAMIQUE ---
                msg_lower = req.message.lower()
                keywords_all = ["tout", "tous", "liste", "énumère", "disponible", "complet", "entier"]
                
                # On affiche 20 résultats si l'utilisateur veut "tout", sinon 5
                limit = 20 if any(word in msg_lower for word in keywords_all) else 5
                
                top_results = filtered[:limit]
                events_formatted = format_events(top_results)
                
                # Ajout du compteur pour la transparence
                count_info = f"\n\n_({len(top_results)} affichés sur {len(filtered)} trouvés)_"
                reply = f"{reply}\n\n{events_formatted}{count_info}"

        # 3. GESTION DE L'HISTORIQUE
        new_history = req.history + [
            {"role": "user", "content": req.message},
            {"role": "assistant", "content": reply}
        ]
        
        return JSONResponse(content={
            "reply": reply, 
            "history": new_history[-6:] 
        })

    except Exception as e:
        logger.error(f"Erreur critique dans /chat/ : {str(e)}")
        return JSONResponse(content={
            "reply": "⚠️ Désolé, je rencontre une petite difficulté technique. Réessayez dans un instant.",
            "history": req.history
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)