import httpx
import logging
from datetime import datetime

from cachetools import TTLCache

# URL de ton API

API_URL = "https://back.lagenda.bj/events/"

cache = TTLCache(maxsize=1, ttl=600)
async def search_events():
    if 'events' in cache:
        return cache['events']
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(API_URL)
            response.raise_for_status()
            data = response.json()
            events = data.get("results", [])
            
            processed_events = []
            for e in events:
                # --- EXTRACTION INTELLIGENTE DES DATES ---
                start_dt = None
                end_dt = None
                
                # Cas 1 : Dates simples (ex: WÀKÀJO)
                if e.get("dates"):
                    raw_date = e["dates"][0]["date"]
                    start_dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                    end_dt = start_dt
                
                # Cas 2 : Dates récurrentes / Plages (ex: Festival Lopo Lopo)
                elif e.get("recurring_dates"):
                    rec = e["recurring_dates"][0]
                    start_dt = datetime.strptime(rec["start_date"], "%Y-%m-%d")
                    end_dt = datetime.strptime(rec["end_date"], "%Y-%m-%d")
                
                # Normalisation pour le filtrage
                e["date_start"] = start_dt
                e["date_end"] = end_dt
                processed_events.append(e)
                
            cache['events'] = processed_events
            return processed_events
    except Exception as e:
        logging.error(f"Erreur API: {e}")
        return []