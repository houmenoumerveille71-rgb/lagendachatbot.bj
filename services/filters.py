#FILTERS.PY
import unicodedata
from datetime import datetime
from difflib import SequenceMatcher

# Dictionnaire de synonymes pour améliorer la recherche
SYNONYMES = {
    "concert": ["musique", "live", "show", "spectacle musical", "performance"],
    "musique": ["concert", "live", "musical", "son", "audio"],
    "festival": ["fest", "festivité", "célébration", "fête"],
    "sport": ["sportif", "athlétisme", "compétition", "match", "tournoi"],
    "football": ["foot", "soccer", "ballon rond"],
    "basketball": ["basket", "nba"],
    "soirée": ["party", "fête", "night", "nuit", "clubbing"],
    "conférence": ["conf", "talk", "présentation", "discours"],
    "formation": ["training", "cours", "apprentissage", "workshop", "atelier"],
    "exposition": ["expo", "galerie", "vernissage", "art"],
    "théâtre": ["pièce", "comédie", "drame", "scène"],
    "danse": ["dancing", "chorégraphie", "ballet", "salsa", "afrobeat"],
    "cinéma": ["film", "movie", "projection", "séance"],
    "gastronomie": ["cuisine", "food", "bouffe", "resto", "dégustation"],
    "enfants": ["kids", "enfant", "jeunesse", "famille", "familial"],
    "business": ["affaires", "entreprise", "entrepreneuriat", "startup", "networking"],
    "tech": ["technologie", "digital", "numérique", "innovation", "it"],
    "bien-être": ["wellness", "santé", "yoga", "méditation", "relaxation", "fitness"],
    "mode": ["fashion", "style", "vêtement", "défilé"],
    "gratuit": ["free", "entrée libre", "sans frais", "offert"]
}

# Catégories principales avec leurs mots-clés associés
CATEGORIES_MAPPING = {
    "musique": ["concert", "musique", "live", "dj", "artiste", "chanteur", "groupe", "band", "jazz", "afrobeat", "hip-hop", "rap", "reggae", "gospel"],
    "festival": ["festival", "fest", "carnaval", "célébration"],
    "sport": ["sport", "football", "foot", "basket", "basketball", "marathon", "course", "match", "tournoi", "compétition", "athlétisme", "boxe", "lutte"],
    "culture": ["théâtre", "danse", "exposition", "expo", "art", "musée", "galerie", "patrimoine", "tradition", "folklore"],
    "cinéma": ["cinéma", "film", "projection", "movie", "court-métrage", "documentaire"],
    "business": ["conférence", "séminaire", "formation", "atelier", "workshop", "networking", "business", "entrepreneuriat", "startup", "tech"],
    "soirée": ["soirée", "party", "fête", "club", "afterwork", "night", "clubbing", "dj"],
    "gastronomie": ["gastronomie", "cuisine", "food", "dégustation", "marché", "restaurant", "chef"],
    "famille": ["enfants", "famille", "jeunesse", "kids", "éducation", "scolaire"],
    "bien-être": ["yoga", "méditation", "fitness", "bien-être", "santé", "wellness", "sport", "gym"],
    "religion": ["église", "mosquée", "prière", "spirituel", "religieux", "cérémonie", "messe"]
}

def normalize(text):
    """Normalise le texte : minuscules, sans accents, sans espaces superflus."""
    if not text: 
        return ""
    text = str(text).lower().strip()
    # Suppression des accents
    text = "".join(c for c in unicodedata.normalize('NFD', text)
                  if unicodedata.category(c) != 'Mn')
    return text

def get_synonyms(word):
    """Retourne les synonymes d'un mot."""
    word_norm = normalize(word)
    synonyms = set([word_norm])
    
    for key, values in SYNONYMES.items():
        key_norm = normalize(key)
        values_norm = [normalize(v) for v in values]
        
        if word_norm == key_norm or word_norm in values_norm:
            synonyms.add(key_norm)
            synonyms.update(values_norm)
    
    return synonyms

def fuzzy_match(text, target, threshold=0.75):
    """Vérifie si deux textes sont similaires (fuzzy matching)."""
    if not text or not target:
        return False
    return SequenceMatcher(None, normalize(text), normalize(target)).ratio() >= threshold

def detect_category(text):
    """Détecte la catégorie d'un événement basé sur son titre/description."""
    text_norm = normalize(text)
    
    scores = {}
    for category, keywords in CATEGORIES_MAPPING.items():
        score = 0
        for keyword in keywords:
            if normalize(keyword) in text_norm:
                score += 1
        if score > 0:
            scores[category] = score
    
    if scores:
        return max(scores, key=scores.get)
    return None

def filter_events(events, filters):
    """
    Filtre et score les événements selon les critères fournis.
    Retourne une liste triée par pertinence.
    """
    scored_results = []
    
    # 1. Extraction des filtres de Gemini
    target_city = normalize(filters.get("city"))
    d_start_str = filters.get("date_start")
    d_end_str = filters.get("date_end")
    search_query = normalize(filters.get("search_query"))
    target_category = normalize(filters.get("category"))
    is_free = filters.get("is_free")

    # Conversion sécurisée des dates
    f_start = None
    f_end = None
    try:
        if d_start_str:
            f_start = datetime.strptime(d_start_str, "%Y-%m-%d").date()
        if d_end_str:
            f_end = datetime.strptime(d_end_str, "%Y-%m-%d").date()
        else:
            f_end = f_start
    except (ValueError, TypeError):
        pass  # Dates invalides ignorées

    for e in events:
        # Créer une copie pour éviter de modifier le cache
        event = e.copy()
        score = 0
        match_reasons = []  # Pour le debug
        
        # Données de l'événement normalisées
        title_norm = normalize(event.get("title", ""))
        desc_norm = normalize(event.get("description", ""))
        city_norm = normalize(event.get("city", ""))
        event_category = normalize(event.get("category", ""))
        
        # Dates de l'événement
        ev_start = event.get("date_start").date() if event.get("date_start") else None
        ev_end = event.get("date_end").date() if event.get("date_end") else ev_start

        # --- ÉTAPE A : FILTRES BLOQUANTS ---

        # 1. Filtre de Ville (Semi-bloquant)
        if target_city:
            city_found = False
            
            # Correspondance exacte dans le champ city
            if target_city in city_norm:
                score += 60
                city_found = True
                match_reasons.append(f"ville_exacte:{target_city}")
            # Correspondance dans la description
            elif target_city in desc_norm:
                score += 25
                city_found = True
                match_reasons.append(f"ville_desc:{target_city}")
            # Fuzzy matching pour les variantes (ex: "Calavi" vs "Abomey-Calavi")
            elif fuzzy_match(target_city, city_norm, 0.6):
                score += 40
                city_found = True
                match_reasons.append(f"ville_fuzzy:{target_city}")
            
            if not city_found:
                continue  # Ville demandée non trouvée, on ignore

        # 2. Filtre de Date (Bloquant si spécifié)
        if f_start and ev_start:
            # Vérifier si l'événement chevauche la période demandée
            event_end = ev_end or ev_start
            if ev_start <= f_end and event_end >= f_start:
                # Bonus si l'événement commence exactement à la date demandée
                if ev_start == f_start:
                    score += 50
                    match_reasons.append("date_exacte")
                else:
                    score += 35
                    match_reasons.append("date_plage")
            else:
                continue  # Hors période, on ignore

        # 3. Filtre Gratuit (Semi-bloquant)
        if is_free is not None:
            event_is_free = event.get("is_free", None)
            event_price = event.get("price", 0)
            
            # Détection si gratuit basée sur le prix ou le champ is_free
            detected_free = event_is_free or event_price == 0 or "gratuit" in desc_norm or "free" in desc_norm
            
            if is_free and detected_free:
                score += 30
                match_reasons.append("gratuit")
            elif is_free and not detected_free:
                score -= 20  # Pénalité mais pas bloquant

        # --- ÉTAPE B : SCORING DE PERTINENCE ---
        
        # 4. Filtre de Catégorie
        if target_category:
            # Catégorie explicite de l'événement
            if target_category in event_category:
                score += 80
                match_reasons.append(f"categorie_exacte:{target_category}")
            else:
                # Détection de catégorie dans le titre/description
                detected_cat = detect_category(title_norm + " " + desc_norm)
                if detected_cat and normalize(detected_cat) == target_category:
                    score += 50
                    match_reasons.append(f"categorie_detectee:{detected_cat}")
                # Recherche des mots-clés de la catégorie
                elif target_category in CATEGORIES_MAPPING:
                    for keyword in CATEGORIES_MAPPING[target_category]:
                        if normalize(keyword) in title_norm:
                            score += 40
                            match_reasons.append(f"categorie_keyword_titre:{keyword}")
                            break
                        elif normalize(keyword) in desc_norm:
                            score += 20
                            match_reasons.append(f"categorie_keyword_desc:{keyword}")
                            break

        # 5. Recherche textuelle avec synonymes
        if search_query:
            words = [w for w in search_query.split() if len(w) > 2]
            found_any = False
            
            for word in words:
                # Obtenir les synonymes du mot
                word_variants = get_synonyms(word)
                
                for variant in word_variants:
                    # Correspondance dans le titre (haute priorité)
                    if variant in title_norm:
                        score += 100
                        found_any = True
                        match_reasons.append(f"mot_titre:{variant}")
                        break
                    # Correspondance dans la description
                    elif variant in desc_norm:
                        score += 35
                        found_any = True
                        match_reasons.append(f"mot_desc:{variant}")
                        break
                
                # Fuzzy matching si pas de correspondance exacte
                if not found_any:
                    title_words = title_norm.split()
                    for tw in title_words:
                        if fuzzy_match(word, tw, 0.8):
                            score += 60
                            found_any = True
                            match_reasons.append(f"mot_fuzzy:{word}~{tw}")
                            break
            
            # Si l'utilisateur a cherché quelque chose de spécifique mais rien trouvé
            if not found_any and len(words) > 0:
                continue  # On ignore cet événement
        else:
            # Pas de recherche spécifique = score de base
            score += 10

        # 6. Bonus pour événements populaires/récents
        if event.get("is_featured"):
            score += 25
            match_reasons.append("featured")
        
        if event.get("views", 0) > 100:
            score += 15
            match_reasons.append("populaire")

        # On garde l'événement s'il a passé les filtres
        if score > 0:
            event["relevance_score"] = score
            event["_match_reasons"] = match_reasons  # Pour debug
            scored_results.append(event)

    # Tri par score (le plus pertinent en haut)
    return sorted(scored_results, key=lambda x: x.get("relevance_score", 0), reverse=True)
