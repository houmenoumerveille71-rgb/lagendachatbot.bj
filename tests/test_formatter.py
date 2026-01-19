# tests/test_formatter.py
"""
Tests unitaires pour le module formatter.py
"""
import pytest
from datetime import datetime
from services.formatter import (
    translate_months,
    clean_html,
    format_date_short,
    format_price,
    format_category,
    format_events,
    month_full,
    month_abbr
)


class TestTranslateMonths:
    """Tests pour la fonction translate_months()"""
    
    def test_translate_full_months(self):
        """Test traduction mois complets"""
        assert translate_months("January", month_full) == "Janvier"
        assert translate_months("February", month_full) == "Février"
        assert translate_months("December", month_full) == "Décembre"
    
    def test_translate_abbr_months(self):
        """Test traduction mois abrégés"""
        assert translate_months("Jan", month_abbr) == "Jan"
        assert translate_months("Feb", month_abbr) == "Fév"
        assert translate_months("Aug", month_abbr) == "Aoû"
    
    def test_translate_in_sentence(self):
        """Test traduction dans une phrase"""
        result = translate_months("20 January 2026", month_full)
        assert "Janvier" in result
        assert "January" not in result


class TestCleanHtml:
    """Tests pour la fonction clean_html()"""
    
    def test_clean_basic_html(self):
        """Test nettoyage HTML basique"""
        assert clean_html("<p>Hello</p>") == "Hello"
        assert clean_html("<strong>Bold</strong>") == "Bold"
    
    def test_clean_nested_html(self):
        """Test nettoyage HTML imbriqué"""
        result = clean_html("<div><p>Nested</p></div>")
        assert result == "Nested"
    
    def test_clean_entities(self):
        """Test nettoyage entités HTML"""
        assert clean_html("Hello&nbsp;World") == "Hello World"
        assert clean_html("Rock&amp;Roll") == "Rock&Roll"
    
    def test_clean_empty(self):
        """Test avec valeurs vides"""
        assert clean_html("") == ""
        assert clean_html(None) == ""
    
    def test_clean_whitespace(self):
        """Test nettoyage espaces"""
        result = clean_html("  Hello  World  ")
        assert result == "Hello  World"


class TestFormatDateShort:
    """Tests pour la fonction format_date_short()"""
    
    def test_format_single_date(self):
        """Test formatage date unique"""
        date = datetime(2026, 1, 20)
        result = format_date_short(date, None)
        assert "20" in result
        # Le mois peut être en majuscule ou minuscule selon la locale
        assert "janvier" in result.lower() or "Janvier" in result
        assert "2026" in result
    
    def test_format_same_day(self):
        """Test formatage même jour"""
        date = datetime(2026, 1, 20)
        result = format_date_short(date, date)
        assert "20" in result
        assert "📅" in result
    
    def test_format_date_range(self):
        """Test formatage plage de dates"""
        start = datetime(2026, 1, 20)
        end = datetime(2026, 1, 25)
        result = format_date_short(start, end)
        assert "Du" in result
        assert "au" in result
    
    def test_format_no_date(self):
        """Test sans date"""
        result = format_date_short(None, None)
        assert "confirmer" in result.lower() or "📅" in result


class TestFormatPrice:
    """Tests pour la fonction format_price()"""
    
    def test_format_free(self):
        """Test événement gratuit"""
        event = {"is_free": True, "price": 0}
        result = format_price(event)
        assert "Gratuit" in result or "🆓" in result
    
    def test_format_paid(self):
        """Test événement payant"""
        event = {"is_free": False, "price": 5000}
        result = format_price(event)
        assert "5" in result
        assert "FCFA" in result or "💰" in result
    
    def test_format_no_price(self):
        """Test sans prix"""
        event = {"is_free": False, "price": 0}
        result = format_price(event)
        # Peut être vide ou "Gratuit"
        assert isinstance(result, str)


class TestFormatCategory:
    """Tests pour la fonction format_category()"""
    
    def test_format_music(self):
        """Test catégorie musique"""
        result = format_category("musique")
        assert "🎵" in result or "Musique" in result
    
    def test_format_sport(self):
        """Test catégorie sport"""
        result = format_category("sport")
        assert "⚽" in result or "Sport" in result
    
    def test_format_culture(self):
        """Test catégorie culture"""
        result = format_category("théâtre")
        assert "🎭" in result or "Théâtre" in result
    
    def test_format_empty(self):
        """Test catégorie vide"""
        result = format_category("")
        assert result == ""
        
        result = format_category(None)
        assert result == ""


class TestFormatEvents:
    """Tests pour la fonction format_events()"""
    
    @pytest.fixture
    def sample_event(self):
        """Événement de test"""
        return {
            "title": "Concert de Jazz",
            "city": "Cotonou",
            "description": "Un super concert de jazz au Palais des Congrès",
            "date_start": datetime(2026, 1, 20),
            "date_end": datetime(2026, 1, 20),
            "link": "https://lagenda.bj/event/1",
            "image": "https://lagenda.bj/images/concert.jpg",
            "category": "musique",
            "is_free": False,
            "price": 5000,
            "venue_name": "Palais des Congrès"
        }
    
    def test_format_single_event(self, sample_event):
        """Test formatage d'un événement"""
        result = format_events([sample_event])
        
        # Vérifier les éléments essentiels
        assert "CONCERT DE JAZZ" in result  # Titre en majuscules
        assert "Cotonou" in result
        assert "lagenda.bj" in result
    
    def test_format_multiple_events(self, sample_event):
        """Test formatage de plusieurs événements"""
        events = [sample_event, sample_event.copy()]
        events[1]["title"] = "Festival Vodoun"
        
        result = format_events(events)
        
        assert "CONCERT DE JAZZ" in result
        assert "FESTIVAL VODOUN" in result
        assert "---" in result  # Séparateur
    
    def test_format_empty_list(self):
        """Test liste vide"""
        result = format_events([])
        assert "Aucun" in result or "trouvé" in result.lower()
    
    def test_format_event_with_image(self, sample_event):
        """Test événement avec image"""
        result = format_events([sample_event])
        assert "![" in result  # Syntaxe Markdown image
        assert sample_event["image"] in result
    
    def test_format_event_without_image(self, sample_event):
        """Test événement sans image"""
        sample_event["image"] = None
        result = format_events([sample_event])
        assert "![" not in result
    
    def test_format_long_description(self, sample_event):
        """Test description longue tronquée"""
        sample_event["description"] = "A" * 200
        result = format_events([sample_event])
        assert "..." in result  # Description tronquée
    
    def test_format_contains_links(self, sample_event):
        """Test présence de liens"""
        result = format_events([sample_event])
        assert "[" in result and "](" in result  # Syntaxe Markdown lien
        assert "Plus d'infos" in result
    
    def test_format_contains_emojis(self, sample_event):
        """Test présence d'emojis"""
        result = format_events([sample_event])
        assert "⭐" in result or "📍" in result or "📅" in result
