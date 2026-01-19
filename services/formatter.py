#FORMATTER.PY
import re

month_full = {
    'January': 'Janvier',
    'February': 'Février',
    'March': 'Mars',
    'April': 'Avril',
    'May': 'Mai',
    'June': 'Juin',
    'July': 'Juillet',
    'August': 'Août',
    'September': 'Septembre',
    'October': 'Octobre',
    'November': 'Novembre',
    'December': 'Décembre'
}

month_abbr = {
    'Jan': 'Jan',
    'Feb': 'Fév',
    'Mar': 'Mar',
    'Apr': 'Avr',
    'May': 'Mai',
    'Jun': 'Jun',
    'Jul': 'Jul',
    'Aug': 'Aoû',
    'Sep': 'Sep',
    'Oct': 'Oct',
    'Nov': 'Nov',
    'Dec': 'Déc'
}

def translate_months(text, month_dict):
    for eng, fr in month_dict.items():
        text = text.replace(eng, fr)
    return text

def clean_html(raw_html):
    """Nettoie le HTML et les entités bizarres des descriptions."""
    if not raw_html:
        return ""
    # Supprime les balises
    text = re.sub(r"<.*?>", "", raw_html)
    # Nettoie les espaces et entités
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("\r\n", " ")
    return text.strip()

def format_date_short(start, end):
    """Formate la date de manière élégante et courte."""
    if not start:
        return "📅 Date à confirmer"

    # Si c'est le même jour
    if not end or start.date() == end.date():
        date_str = start.strftime('%d %B %Y')
        return f"📅 {translate_months(date_str, month_full)}"

    # Si c'est une plage (ex: Festival)
    start_str = start.strftime('%d %b')
    end_str = end.strftime('%d %b %Y')
    return f"📅 Du {translate_months(start_str, month_abbr)} au {translate_months(end_str, month_abbr)}"

def format_price(event):
    """Formate le prix de l'événement."""
    if event.get("is_free"):
        return "🆓 Gratuit"
    
    price = event.get("price", 0)
    if price and price > 0:
        return f"💰 {int(price):,} FCFA".replace(",", " ")
    
    return ""

def format_category(category):
    """Formate la catégorie avec un emoji approprié."""
    if not category:
        return ""
    
    category_emojis = {
        "musique": "🎵",
        "concert": "🎤",
        "festival": "🎪",
        "sport": "⚽",
        "football": "⚽",
        "basketball": "🏀",
        "culture": "🎭",
        "théâtre": "🎭",
        "danse": "💃",
        "cinéma": "🎬",
        "exposition": "🖼️",
        "art": "🎨",
        "conférence": "🎤",
        "formation": "📚",
        "business": "💼",
        "soirée": "🌙",
        "gastronomie": "🍽️",
        "famille": "👨‍👩‍👧‍👦",
        "enfants": "👶",
        "bien-être": "🧘",
        "religion": "🙏",
        "mode": "👗"
    }
    
    cat_lower = category.lower()
    emoji = "🏷️"
    for key, em in category_emojis.items():
        if key in cat_lower:
            emoji = em
            break
    
    return f"{emoji} {category.capitalize()}"

def format_events(events):
    """Transforme les dictionnaires d'événements en messages élégants."""
    if not events:
        return "📍 *Note :* Aucun événement trouvé pour ces critères."

    formatted_blocks = []

    for e in events:
        # 1. Préparation des données
        title = (e.get("title") or "Événement").upper()
        city = e.get("city") or "Bénin"
        link = e.get("link") or "https://lagenda.bj"
        img = e.get("image")
        category = e.get("category")
        venue = e.get("venue_name", "")
        
        # 2. Description courte (max 120 caractères pour le mobile)
        desc = clean_html(e.get("description", ""))
        desc_short = (desc[:117] + "...") if len(desc) > 120 else desc

        # 3. Construction du bloc Markdown
        # On met le titre en gras et en lien
        block = f"⭐ **[{title}]({link})**\n"
        
        # Ligne lieu et date
        location_parts = [city]
        if venue and venue != city:
            location_parts.append(venue)
        block += f"📍 {' - '.join(location_parts)} | {format_date_short(e.get('date_start'), e.get('date_end'))}\n"
        
        # Ligne catégorie et prix
        meta_parts = []
        if category:
            cat_formatted = format_category(category)
            if cat_formatted:
                meta_parts.append(cat_formatted)
        
        price_formatted = format_price(e)
        if price_formatted:
            meta_parts.append(price_formatted)
        
        if meta_parts:
            block += f"{' | '.join(meta_parts)}\n"
        
        # 4. Image (Syntaxe Markdown gérée par ton JS)
        if img:
            block += f"![affiche]({img})\n"
            
        if desc_short:
            block += f"📝 _{desc_short}_\n"
            
        block += f"🔗 [Plus d'infos]({link})"
        
        formatted_blocks.append(block)

    # Séparateur visuel entre les événements
    return "\n\n---\n\n".join(formatted_blocks)