#TOOLS.PY
import httpx
import logging
from datetime import datetime

from cachetools import TTLCache

# URL de ton API
API_URL = "https://back.lagenda.bj/events/"

# Cache avec TTL de 10 minutes
cache = TTLCache(maxsize=1, ttl=600)

async def search_events():
    """
    Récupère et normalise les événements depuis l'API.
    Utilise un cache pour éviter les appels répétitifs.
    """
    if 'events' in cache:
        logging.info("Événements récupérés depuis le cache")
        return cache['events']
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(API_URL)
            response.raise_for_status()
            data = response.json()
            events = data.get("results", [])
            
            logging.info(f"API: {len(events)} événements récupérés")
            
            processed_events = []
            for e in events:
                try:
                    # --- EXTRACTION INTELLIGENTE DES DATES ---
                    start_dt = None
                    end_dt = None
                    
                    # Cas 1 : Dates simples (ex: WÀKÀJO)
                    dates_list = e.get("dates", [])
                    if dates_list and len(dates_list) > 0:
                        raw_date = dates_list[0].get("date")
                        if raw_date:
                            start_dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                            end_dt = start_dt
                    
                    # Cas 2 : Dates récurrentes / Plages (ex: Festival Lopo Lopo)
                    recurring_list = e.get("recurring_dates", [])
                    if not start_dt and recurring_list and len(recurring_list) > 0:
                        rec = recurring_list[0]
                        if rec.get("start_date"):
                            start_dt = datetime.strptime(rec["start_date"], "%Y-%m-%d")
                        if rec.get("end_date"):
                            end_dt = datetime.strptime(rec["end_date"], "%Y-%m-%d")
                        else:
                            end_dt = start_dt
                    
                    # --- EXTRACTION DES MÉTADONNÉES ---
                    
                    # Catégorie
                    category = None
                    if e.get("category"):
                        if isinstance(e["category"], dict):
                            category = e["category"].get("name", "")
                        else:
                            category = str(e["category"])
                    
                    # Prix et gratuité
                    price = 0
                    is_free = False
                    if e.get("price"):
                        try:
                            price = float(e["price"])
                        except (ValueError, TypeError):
                            price = 0
                    
                    if e.get("is_free") or price == 0:
                        is_free = True
                    
                    # Vérification dans la description pour "gratuit"
                    desc = str(e.get("description", "")).lower()
                    if "gratuit" in desc or "entrée libre" in desc or "free" in desc:
                        is_free = True
                    
                    # Popularité
                    views = e.get("views", 0) or 0
                    is_featured = e.get("is_featured", False) or e.get("featured", False)
                    
                    # Lieu
                    venue = e.get("venue", {})
                    if isinstance(venue, dict):
                        venue_name = venue.get("name", "")
                    else:
                        venue_name = str(venue) if venue else ""
                    
                    # Normalisation pour le filtrage
                    e["date_start"] = start_dt
                    e["date_end"] = end_dt
                    e["category"] = category
                    e["price"] = price
                    e["is_free"] = is_free
                    e["views"] = views
                    e["is_featured"] = is_featured
                    e["venue_name"] = venue_name
                    
                    processed_events.append(e)
                    
                except Exception as parse_error:
                    logging.warning(f"Erreur parsing événement: {parse_error}")
                    # On ajoute quand même l'événement avec des valeurs par défaut
                    e["date_start"] = None
                    e["date_end"] = None
                    processed_events.append(e)
                
            cache['events'] = processed_events
            return processed_events
            
    except httpx.TimeoutException:
        logging.error("Timeout lors de l'appel API")
        return []
    except httpx.HTTPStatusError as e:
        logging.error(f"Erreur HTTP API: {e.response.status_code}")
        return []
    except Exception as e:
        logging.error(f"Erreur API inattendue: {e}")
        return []