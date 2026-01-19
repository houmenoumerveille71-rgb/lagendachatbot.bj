# tests/test_tools.py
"""
Tests unitaires pour le module tools.py
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import asyncio

# Import du module à tester
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.tools import search_events, cache


class TestSearchEventsSync:
    """Tests synchrones pour search_events() - utilise asyncio.run()"""
    
    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Vider le cache avant chaque test"""
        cache.clear()
        yield
        cache.clear()
    
    @pytest.fixture
    def mock_api_response(self):
        """Réponse API simulée"""
        return {
            "results": [
                {
                    "title": "Concert de Jazz",
                    "city": "Cotonou",
                    "description": "Un super concert",
                    "dates": [{"date": "2026-01-20T20:00:00Z"}],
                    "category": {"name": "Musique"},
                    "price": 5000,
                    "is_free": False,
                    "link": "https://lagenda.bj/event/1",
                    "image": "https://lagenda.bj/images/1.jpg"
                },
                {
                    "title": "Festival Vodoun",
                    "city": "Ouidah",
                    "description": "Festival culturel gratuit",
                    "recurring_dates": [
                        {"start_date": "2026-01-10", "end_date": "2026-01-12"}
                    ],
                    "category": "Culture",
                    "price": 0,
                    "is_free": True,
                    "link": "https://lagenda.bj/event/2"
                }
            ]
        }
    
    def test_search_events_success(self, mock_api_response):
        """Test récupération réussie des événements"""
        async def run_test():
            with patch('services.tools.httpx.AsyncClient') as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_api_response
                mock_response.raise_for_status = MagicMock()
                
                mock_client_instance = AsyncMock()
                mock_client_instance.get.return_value = mock_response
                mock_client_instance.__aenter__.return_value = mock_client_instance
                mock_client_instance.__aexit__.return_value = None
                mock_client.return_value = mock_client_instance
                
                result = await search_events()
                
                assert len(result) == 2
                assert result[0]["title"] == "Concert de Jazz"
                assert result[1]["title"] == "Festival Vodoun"
        
        asyncio.run(run_test())
    
    def test_search_events_cache(self, mock_api_response):
        """Test que le cache fonctionne"""
        async def run_test():
            with patch('services.tools.httpx.AsyncClient') as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_api_response
                mock_response.raise_for_status = MagicMock()
                
                mock_client_instance = AsyncMock()
                mock_client_instance.get.return_value = mock_response
                mock_client_instance.__aenter__.return_value = mock_client_instance
                mock_client_instance.__aexit__.return_value = None
                mock_client.return_value = mock_client_instance
                
                # Premier appel
                result1 = await search_events()
                # Deuxième appel (devrait utiliser le cache)
                result2 = await search_events()
                
                # L'API ne devrait être appelée qu'une fois
                assert mock_client_instance.get.call_count == 1
                assert result1 == result2
        
        asyncio.run(run_test())
    
    def test_search_events_api_error(self):
        """Test gestion erreur API"""
        async def run_test():
            with patch('services.tools.httpx.AsyncClient') as mock_client:
                mock_client_instance = AsyncMock()
                mock_client_instance.get.side_effect = Exception("API Error")
                mock_client_instance.__aenter__.return_value = mock_client_instance
                mock_client_instance.__aexit__.return_value = None
                mock_client.return_value = mock_client_instance
                
                result = await search_events()
                
                assert result == []
        
        asyncio.run(run_test())
    
    def test_search_events_timeout(self):
        """Test gestion timeout"""
        import httpx
        
        async def run_test():
            with patch('services.tools.httpx.AsyncClient') as mock_client:
                mock_client_instance = AsyncMock()
                mock_client_instance.get.side_effect = httpx.TimeoutException("Timeout")
                mock_client_instance.__aenter__.return_value = mock_client_instance
                mock_client_instance.__aexit__.return_value = None
                mock_client.return_value = mock_client_instance
                
                result = await search_events()
                
                assert result == []
        
        asyncio.run(run_test())
    
    def test_search_events_date_parsing(self, mock_api_response):
        """Test parsing des dates"""
        async def run_test():
            with patch('services.tools.httpx.AsyncClient') as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_api_response
                mock_response.raise_for_status = MagicMock()
                
                mock_client_instance = AsyncMock()
                mock_client_instance.get.return_value = mock_response
                mock_client_instance.__aenter__.return_value = mock_client_instance
                mock_client_instance.__aexit__.return_value = None
                mock_client.return_value = mock_client_instance
                
                result = await search_events()
                
                # Vérifier que les dates sont parsées
                assert result[0]["date_start"] is not None
                assert isinstance(result[0]["date_start"], datetime)
                
                # Vérifier les dates récurrentes
                assert result[1]["date_start"] is not None
                assert result[1]["date_end"] is not None
        
        asyncio.run(run_test())
    
    def test_search_events_metadata_extraction(self, mock_api_response):
        """Test extraction des métadonnées"""
        async def run_test():
            with patch('services.tools.httpx.AsyncClient') as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_api_response
                mock_response.raise_for_status = MagicMock()
                
                mock_client_instance = AsyncMock()
                mock_client_instance.get.return_value = mock_response
                mock_client_instance.__aenter__.return_value = mock_client_instance
                mock_client_instance.__aexit__.return_value = None
                mock_client.return_value = mock_client_instance
                
                result = await search_events()
                
                # Vérifier l'extraction de la catégorie
                assert result[0]["category"] == "Musique"
                
                # Vérifier l'extraction du prix
                assert result[0]["price"] == 5000
                assert result[0]["is_free"] == False
                
                # Vérifier la détection gratuit
                assert result[1]["is_free"] == True
        
        asyncio.run(run_test())
    
    def test_search_events_empty_dates(self):
        """Test événement sans dates"""
        api_response = {
            "results": [
                {
                    "title": "Event sans date",
                    "city": "Cotonou",
                    "dates": [],
                    "recurring_dates": []
                }
            ]
        }
        
        async def run_test():
            with patch('services.tools.httpx.AsyncClient') as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = api_response
                mock_response.raise_for_status = MagicMock()
                
                mock_client_instance = AsyncMock()
                mock_client_instance.get.return_value = mock_response
                mock_client_instance.__aenter__.return_value = mock_client_instance
                mock_client_instance.__aexit__.return_value = None
                mock_client.return_value = mock_client_instance
                
                result = await search_events()
                
                # Ne devrait pas crasher
                assert len(result) == 1
                assert result[0]["date_start"] is None
        
        asyncio.run(run_test())
    
    def test_search_events_empty_results(self):
        """Test réponse API vide"""
        api_response = {"results": []}
        
        async def run_test():
            with patch('services.tools.httpx.AsyncClient') as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = api_response
                mock_response.raise_for_status = MagicMock()
                
                mock_client_instance = AsyncMock()
                mock_client_instance.get.return_value = mock_response
                mock_client_instance.__aenter__.return_value = mock_client_instance
                mock_client_instance.__aexit__.return_value = None
                mock_client.return_value = mock_client_instance
                
                result = await search_events()
                
                assert result == []
        
        asyncio.run(run_test())
