import unicodedata
from datetime import datetime

def normalize(text):
    if not text: return ""
    text = text.lower().strip()
    return "".join(c for c in unicodedata.normalize('NFD', text)
                  if unicodedata.category(c) != 'Mn')

def filter_events(events, filters):
    scored_results = []
    
    # 1. Extraction des filtres de Gemini
    target_city = normalize(filters.get("city"))
    d_start_str = filters.get("date_start")
    d_end_str = filters.get("date_end")
    search_query = normalize(filters.get("search_query"))

    # Conversion des dates pour la comparaison
    f_start = datetime.strptime(d_start_str, "%Y-%m-%d").date() if d_start_str else None
    f_end = datetime.strptime(d_end_str, "%Y-%m-%d").date() if d_end_str else f_start

    for e in events:
        score = 0
        
        # Données de l'événement
        title_norm = normalize(e.get("title", ""))
        desc_norm = normalize(e.get("description", ""))
        city_norm = normalize(e.get("city", ""))
        ev_start = e.get("date_start").date() if e.get("date_start") else None
        ev_end = e.get("date_end").date() if e.get("date_end") else ev_start

        # --- ÉTAPE A : LES FILTRES SEMI-BLOQUANTS ---

        # 1. Filtre de Ville (Souple)
        # Si une ville est demandée, mais qu'elle n'est ni dans le champ city ni dans la desc, on pénalise lourdement au lieu d'exclure
        if target_city:
            if target_city in city_norm:
                score += 50 # Bonus ville exacte
            elif target_city in desc_norm:
                score += 20 # Bonus ville mentionnée
            else:
                continue # Si la ville demandée n'existe nulle part, on ignore

        # 2. Filtre de Date (Large)
        if f_start and ev_start:
            # Si l'événement est dans la plage demandée
            if ev_start <= f_end and (ev_end or ev_start) >= f_start:
                score += 40
            else:
                # Si on cherche un truc précis (ex: "ce soir"), on exclut ce qui n'est pas à date
                # Mais si c'est une recherche générale, on peut être plus souple.
                # Ici on reste strict sur la date pour éviter le hors-sujet temporel.
                continue

        # --- ÉTAPE B : SCORING DE PERTINENCE (Le "Cerveau") ---
        
        if search_query:
            words = [w for w in search_query.split() if len(w) > 2]
            found_word = False
            
            for word in words:
                if word in title_norm:
                    score += 100
                    found_word = True
                if word in desc_norm:
                    score += 30
                    found_word = True
            
            # Si l'utilisateur a tapé un mot-clé mais qu'il n'est nulle part
            if not found_word:
                continue
        else:
            # Si pas de recherche spécifique, on donne un score de base
            score += 10

        # On garde l'événement s'il a passé les filtres
        e["relevance_score"] = score
        scored_results.append(e)

    # Tri par score (le plus pertinent en haut)
    return sorted(scored_results, key=lambda x: x["relevance_score"], reverse=True)