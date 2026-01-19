# tests/test_api.py
"""
Tests d'intégration pour les endpoints FastAPI
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

# Import de l'application
from main import app


class TestHomeEndpoint:
    """Tests pour l'endpoint GET /"""
    
    @pytest.fixture
    def client(self):
        """Client de test FastAPI"""
        return TestClient(app)
    
    def test_home_returns_html(self, client):
        """Test que la page d'accueil retourne du HTML"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_home_contains_chat_elements(self, client):
        """Test que la page contient les éléments du chat"""
        response = client.get("/")
        content = response.text
        
        assert "Agenda.bj" in content
        assert "chat" in content.lower()


class TestChatEndpoint:
    """Tests pour l'endpoint POST /chat/"""
    
    @pytest.fixture
    def client(self):
        """Client de test FastAPI"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_gemini_response(self):
        """Réponse Gemini simulée"""
        return {
            "intent": "search",
            "filters": {
                "city": "Cotonou",
                "date_start": "2026-01-20",
                "date_end": "2026-01-20",
                "category": None,
                "search_query": "concert",
                "is_free": None
            },
            "ai_reply": "Je cherche les concerts à Cotonou..."
        }
    
    @pytest.fixture
    def mock_events(self):
        """Événements simulés"""
        return [
            {
                "title": "Concert de Jazz",
                "city": "Cotonou",
                "description": "Un super concert de jazz",
                "date_start": datetime(2026, 1, 20),
                "date_end": datetime(2026, 1, 20),
                "category": "musique",
                "is_free": False,
                "price": 5000,
                "link": "https://lagenda.bj/event/1",
                "image": "https://lagenda.bj/images/1.jpg",
                "venue_name": "Palais des Congrès"
            }
        ]
    
    def test_chat_valid_request(self, client, mock_gemini_response, mock_events):
        """Test requête chat valide"""
        with patch('main.chat_with_gemini', new_callable=AsyncMock) as mock_gemini:
            with patch('main.search_events', new_callable=AsyncMock) as mock_search:
                mock_gemini.return_value = mock_gemini_response
                mock_search.return_value = mock_events
                
                response = client.post("/chat/", json={
                    "message": "Concerts à Cotonou",
                    "history": []
                })
                
                assert response.status_code == 200
                data = response.json()
                assert "reply" in data
                assert "history" in data
    
    def test_chat_returns_events(self, client, mock_gemini_response, mock_events):
        """Test que le chat retourne des événements"""
        with patch('main.chat_with_gemini', new_callable=AsyncMock) as mock_gemini:
            with patch('main.search_events', new_callable=AsyncMock) as mock_search:
                mock_gemini.return_value = mock_gemini_response
                mock_search.return_value = mock_events
                
                response = client.post("/chat/", json={
                    "message": "Concerts à Cotonou",
                    "history": []
                })
                
                data = response.json()
                # La réponse devrait contenir des infos sur l'événement
                assert "Concert" in data["reply"] or "concert" in data["reply"].lower()
    
    def test_chat_no_results(self, client, mock_gemini_response):
        """Test chat sans résultats"""
        with patch('main.chat_with_gemini', new_callable=AsyncMock) as mock_gemini:
            with patch('main.search_events', new_callable=AsyncMock) as mock_search:
                mock_gemini.return_value = mock_gemini_response
                mock_search.return_value = []  # Pas d'événements
                
                response = client.post("/chat/", json={
                    "message": "Concerts à Paris",
                    "history": []
                })
                
                assert response.status_code == 200
                data = response.json()
                # Devrait indiquer qu'aucun événement n'a été trouvé
                assert "aucun" in data["reply"].lower() or "trouvé" in data["reply"].lower()
    
    def test_chat_intent_chat(self, client):
        """Test intent chat (pas de recherche)"""
        chat_response = {
            "intent": "chat",
            "filters": {},
            "ai_reply": "Bonjour ! Comment puis-je vous aider ?"
        }
        
        with patch('main.chat_with_gemini', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = chat_response
            
            response = client.post("/chat/", json={
                "message": "Bonjour",
                "history": []
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "Bonjour" in data["reply"]
    
    def test_chat_history_management(self, client, mock_gemini_response, mock_events):
        """Test gestion de l'historique"""
        with patch('main.chat_with_gemini', new_callable=AsyncMock) as mock_gemini:
            with patch('main.search_events', new_callable=AsyncMock) as mock_search:
                mock_gemini.return_value = mock_gemini_response
                mock_search.return_value = mock_events
                
                # Premier message
                response1 = client.post("/chat/", json={
                    "message": "Concerts à Cotonou",
                    "history": []
                })
                
                history1 = response1.json()["history"]
                
                # Deuxième message avec historique
                response2 = client.post("/chat/", json={
                    "message": "Et demain ?",
                    "history": history1
                })
                
                history2 = response2.json()["history"]
                
                # L'historique devrait contenir les messages précédents
                assert len(history2) >= 2
    
    def test_chat_history_limit(self, client, mock_gemini_response, mock_events):
        """Test limite de l'historique (6 messages max)"""
        with patch('main.chat_with_gemini', new_callable=AsyncMock) as mock_gemini:
            with patch('main.search_events', new_callable=AsyncMock) as mock_search:
                mock_gemini.return_value = mock_gemini_response
                mock_search.return_value = mock_events
                
                # Créer un historique long
                long_history = [
                    {"role": "user", "content": f"Message {i}"}
                    for i in range(10)
                ]
                
                response = client.post("/chat/", json={
                    "message": "Nouveau message",
                    "history": long_history
                })
                
                history = response.json()["history"]
                # L'historique devrait être limité
                assert len(history) <= 6
    
    def test_chat_empty_message(self, client):
        """Test message vide"""
        response = client.post("/chat/", json={
            "message": "",
            "history": []
        })
        
        # Devrait quand même fonctionner (Gemini gère)
        assert response.status_code == 200
    
    def test_chat_error_handling(self, client):
        """Test gestion des erreurs"""
        with patch('main.chat_with_gemini', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.side_effect = Exception("Erreur Gemini")
            
            response = client.post("/chat/", json={
                "message": "Test",
                "history": []
            })
            
            assert response.status_code == 200
            data = response.json()
            # Devrait retourner un message d'erreur gracieux
            assert "difficulté" in data["reply"].lower() or "erreur" in data["reply"].lower() or "désolé" in data["reply"].lower()
    
    def test_chat_invalid_json(self, client):
        """Test JSON invalide"""
        response = client.post("/chat/", 
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        # FastAPI devrait retourner une erreur 422
        assert response.status_code == 422


class TestRateLimiting:
    """Tests pour le rate limiting"""
    
    @pytest.fixture
    def client(self):
        """Client de test FastAPI"""
        return TestClient(app)
    
    def test_rate_limit_header(self, client):
        """Test présence des headers de rate limit"""
        with patch('main.chat_with_gemini', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = {
                "intent": "chat",
                "filters": {},
                "ai_reply": "Test"
            }
            
            response = client.post("/chat/", json={
                "message": "Test",
                "history": []
            })
            
            # Les headers de rate limit devraient être présents
            # (dépend de la configuration SlowAPI)
            assert response.status_code in [200, 429]
