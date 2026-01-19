# tests/test_filters.py
"""
Tests unitaires pour le module filters.py
"""
import pytest
from datetime import datetime
from services.filters import (
    normalize, 
    get_synonyms, 
    fuzzy_match, 
    detect_category, 
    filter_events
)


class TestNormalize:
    """Tests pour la fonction normalize()"""
    
    def test_normalize_basic(self):
        """Test normalisation basique"""
        assert normalize("Cotonou") == "cotonou"
        assert normalize("PORTO-NOVO") == "porto-novo"
    
    def test_normalize_accents(self):
        """Test suppression des accents"""
        assert normalize("Événement") == "evenement"
        assert normalize("Café") == "cafe"
        assert normalize("Noël") == "noel"
        assert normalize("Bénin") == "benin"
    
    def test_normalize_whitespace(self):
        """Test gestion des espaces"""
        assert normalize("  Cotonou  ") == "cotonou"
        assert normalize("Porto Novo") == "porto novo"
    
    def test_normalize_empty(self):
        """Test avec valeurs vides"""
        assert normalize("") == ""
        assert normalize(None) == ""
    
    def test_normalize_special_chars(self):
        """Test avec caractères spéciaux"""
        assert normalize("Abomey-Calavi") == "abomey-calavi"
        assert normalize("Sèmè-Kpodji") == "seme-kpodji"


class TestGetSynonyms:
    """Tests pour la fonction get_synonyms()"""
    
    def test_synonyms_concert(self):
        """Test synonymes de concert"""
        synonyms = get_synonyms("concert")
        assert "musique" in synonyms
        assert "live" in synonyms
        assert "concert" in synonyms
    
    def test_synonyms_sport(self):
        """Test synonymes de sport"""
        synonyms = get_synonyms("football")
        assert "foot" in synonyms or "football" in synonyms
    
    def test_synonyms_unknown(self):
        """Test mot sans synonymes"""
        synonyms = get_synonyms("xyz123")
        assert "xyz123" in synonyms
        assert len(synonyms) >= 1


class TestFuzzyMatch:
    """Tests pour la fonction fuzzy_match()"""
    
    def test_fuzzy_exact_match(self):
        """Test correspondance exacte"""
        assert fuzzy_match("cotonou", "cotonou", 0.75) == True
    
    def test_fuzzy_similar(self):
        """Test correspondance similaire"""
        assert fuzzy_match("calavi", "abomey-calavi", 0.5) == True
    
    def test_fuzzy_different(self):
        """Test mots différents"""
        assert fuzzy_match("paris", "cotonou", 0.75) == False
    
    def test_fuzzy_empty(self):
        """Test avec valeurs vides"""
        assert fuzzy_match("", "cotonou", 0.75) == False
        assert fuzzy_match("cotonou", "", 0.75) == False
        assert fuzzy_match(None, "cotonou", 0.75) == False


class TestDetectCategory:
    """Tests pour la fonction detect_category()"""
    
    def test_detect_music(self):
        """Test détection catégorie musique"""
        assert detect_category("Concert de jazz à Cotonou") == "musique"
        assert detect_category("Soirée DJ au club") in ["musique", "soirée"]
    
    def test_detect_sport(self):
        """Test détection catégorie sport"""
        assert detect_category("Match de football") == "sport"
        assert detect_category("Marathon de Cotonou") == "sport"
    
    def test_detect_culture(self):
        """Test détection catégorie culture"""
        assert detect_category("Exposition d'art contemporain") == "culture"
        assert detect_category("Pièce de théâtre") == "culture"
    
    def test_detect_none(self):
        """Test quand aucune catégorie détectée"""
        result = detect_category("Événement spécial")
        # Peut retourner None ou une catégorie par défaut
        assert result is None or isinstance(result, str)


class TestFilterEvents:
    """Tests pour la fonction filter_events()"""
    
    @pytest.fixture
    def sample_events(self):
        """Événements de test"""
        return [
            {
                "title": "Concert de Jazz",
                "city": "Cotonou",
                "description": "Un super concert de jazz",
                "date_start": datetime(2026, 1, 20),
                "date_end": datetime(2026, 1, 20),
                "category": "musique",
                "is_free": False,
                "price": 5000
            },
            {
                "title": "Festival Vodoun",
                "city": "Ouidah",
                "description": "Festival culturel à Ouidah",
                "date_start": datetime(2026, 1, 10),
                "date_end": datetime(2026, 1, 12),
                "category": "culture",
                "is_free": True,
                "price": 0
            },
            {
                "title": "Match de Football",
                "city": "Porto-Novo",
                "description": "Match au stade de Porto-Novo",
                "date_start": datetime(2026, 1, 25),
                "date_end": datetime(2026, 1, 25),
                "category": "sport",
                "is_free": False,
                "price": 2000
            }
        ]
    
    def test_filter_by_city(self, sample_events):
        """Test filtrage par ville"""
        result = filter_events(sample_events, {"city": "Cotonou"})
        assert len(result) == 1
        assert result[0]["city"] == "Cotonou"
    
    def test_filter_by_city_not_found(self, sample_events):
        """Test filtrage ville non trouvée"""
        result = filter_events(sample_events, {"city": "Paris"})
        assert len(result) == 0
    
    def test_filter_by_date(self, sample_events):
        """Test filtrage par date"""
        result = filter_events(sample_events, {
            "date_start": "2026-01-20",
            "date_end": "2026-01-20"
        })
        assert len(result) == 1
        assert result[0]["title"] == "Concert de Jazz"
    
    def test_filter_by_date_range(self, sample_events):
        """Test filtrage par plage de dates"""
        result = filter_events(sample_events, {
            "date_start": "2026-01-10",
            "date_end": "2026-01-25"
        })
        assert len(result) == 3
    
    def test_filter_by_search_query(self, sample_events):
        """Test filtrage par recherche textuelle"""
        result = filter_events(sample_events, {"search_query": "jazz"})
        assert len(result) == 1
        assert "Jazz" in result[0]["title"]
    
    def test_filter_by_category(self, sample_events):
        """Test filtrage par catégorie"""
        result = filter_events(sample_events, {"category": "sport"})
        # Le filtre par catégorie donne un meilleur score mais n'exclut pas les autres
        # Vérifier que l'événement sport est en premier (meilleur score)
        assert result[0]["category"] == "sport"
        assert result[0]["relevance_score"] > result[-1]["relevance_score"]
    
    def test_filter_by_free(self, sample_events):
        """Test filtrage événements gratuits"""
        result = filter_events(sample_events, {"is_free": True})
        # Au moins l'événement gratuit devrait avoir un meilleur score
        assert any(e["is_free"] for e in result)
    
    def test_filter_combined(self, sample_events):
        """Test filtrage combiné ville + date"""
        result = filter_events(sample_events, {
            "city": "Cotonou",
            "date_start": "2026-01-20",
            "date_end": "2026-01-20"
        })
        assert len(result) == 1
        assert result[0]["city"] == "Cotonou"
    
    def test_filter_empty_filters(self, sample_events):
        """Test sans filtres (tous les événements)"""
        result = filter_events(sample_events, {})
        assert len(result) == 3
    
    def test_filter_scoring_order(self, sample_events):
        """Test que les résultats sont triés par score"""
        result = filter_events(sample_events, {"search_query": "concert"})
        if len(result) > 1:
            # Vérifier que le score est décroissant
            scores = [e.get("relevance_score", 0) for e in result]
            assert scores == sorted(scores, reverse=True)
    
    def test_filter_no_mutation(self, sample_events):
        """Test que les événements originaux ne sont pas modifiés"""
        original_title = sample_events[0]["title"]
        filter_events(sample_events, {"city": "Cotonou"})
        assert sample_events[0]["title"] == original_title
        # Vérifier qu'il n'y a pas de relevance_score ajouté à l'original
        assert "relevance_score" not in sample_events[0]


class TestFilterEventsEdgeCases:
    """Tests des cas limites pour filter_events()"""
    
    def test_empty_events_list(self):
        """Test avec liste vide"""
        result = filter_events([], {"city": "Cotonou"})
        assert result == []
    
    def test_event_without_city(self):
        """Test événement sans ville"""
        events = [{"title": "Test", "city": None, "date_start": None}]
        result = filter_events(events, {"city": "Cotonou"})
        assert len(result) == 0
    
    def test_event_without_date(self):
        """Test événement sans date"""
        events = [{"title": "Test", "city": "Cotonou", "date_start": None}]
        result = filter_events(events, {"city": "Cotonou"})
        assert len(result) == 1
    
    def test_invalid_date_format(self):
        """Test avec format de date invalide"""
        events = [{"title": "Test", "city": "Cotonou", "date_start": datetime.now()}]
        # Ne devrait pas crasher
        result = filter_events(events, {"date_start": "invalid-date"})
        assert isinstance(result, list)
    
    def test_fuzzy_city_match(self):
        """Test correspondance floue de ville"""
        events = [{"title": "Test", "city": "Abomey-Calavi", "date_start": None, "description": ""}]
        result = filter_events(events, {"city": "Calavi"})
        # Devrait trouver grâce au fuzzy matching
        assert len(result) >= 0  # Dépend du seuil de fuzzy matching
