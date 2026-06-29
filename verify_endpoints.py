import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add current folder to sys.path to find 'app'
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

class TestEduGenieEndpoints(unittest.TestCase):
    """
    Test suite verifying FastAPI endpoints.
    Uses mock wrappers for AI APIs to ensure validation code works and returns correct schemas.
    """

    def setUp(self):
        # Prevent actually loading local LaMini or calling Gemini APIs in our unit checks
        self.gemini_patcher = patch("app.ai.gemini.gemini_client.generate")
        self.lamini_patcher = patch("app.ai.lamini.lamini_client.generate")
        self.mock_gemini = self.gemini_patcher.start()
        self.mock_lamini = self.lamini_patcher.start()
        
        # Configure default return responses
        self.mock_gemini.return_value = "This is a mock response from Gemini API."
        self.mock_lamini.return_value = "This is a mock response from local LaMini."

    def tearDown(self):
        self.gemini_patcher.stop()
        self.lamini_patcher.stop()

    def test_health_endpoint(self):
        """Verifies health check endpoints return 200 and connectivity statuses."""
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "operational")
        self.assertIn("gemini_api_set", data)
        self.assertIn("default_provider", data)

    def test_index_render(self):
        """Verifies GET / returns the index page template."""
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("EduGenie", response.text)

    def test_qa_endpoint(self):
        """Verifies POST /qa validates schemas and routes queries."""
        payload = {"question": "What is the capital of France?", "model_preference": "gemini"}
        response = client.post("/qa", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["question"], "What is the capital of France?")
        self.assertIn("answer", data)
        self.assertEqual(data["model_used"], "Gemini 1.5 Pro")

    def test_qa_endpoint_validation_failure(self):
        """Verifies QA route rejects questions that are too short."""
        payload = {"question": "Why?", "model_preference": "gemini"} # min_length is 5
        response = client.post("/qa", json=payload)
        self.assertEqual(response.status_code, 422) # Unprocessable Entity

    def test_explain_endpoint(self):
        """Verifies POST /explain structures concept explanations."""
        payload = {"concept": "Recursion", "level": "Beginner", "model_preference": "gemini"}
        response = client.post("/explain", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["concept"], "Recursion")
        self.assertEqual(data["level"], "Beginner")
        self.assertIn("explanation", data)

    def test_summarize_endpoint(self):
        """Verifies POST /summarize handles notes and formats summaries."""
        payload = {
            "text": "Photosynthesis is a process used by plants and other organisms to convert light energy into chemical energy.",
            "format": "Concise",
            "model_preference": "gemini"
        }
        response = client.post("/summarize", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("summary", data)
        self.assertEqual(data["format"], "Concise")
        self.assertGreater(data["original_length"], 0)

    @patch("app.services.education_service.parse_json_from_llm")
    def test_quiz_endpoint(self, mock_parse_json):
        """Verifies POST /quiz creates interactive multiple choice items."""
        # Set mock JSON response
        mock_quiz_data = [
            {
                "questionText": "What is 2+2?",
                "options": ["3", "4", "5", "6"],
                "correctAnswer": "4",
                "explanation": "Simple arithmetic."
            }
        ]
        mock_parse_json.return_value = mock_quiz_data
        
        payload = {"topic": "Math", "difficulty": "Easy", "num_questions": 1, "model_preference": "gemini"}
        response = client.post("/quiz", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["topic"], "Math")
        self.assertEqual(data["difficulty"], "Easy")
        self.assertEqual(len(data["questions"]), 1)
        self.assertEqual(data["questions"][0]["questionText"], "What is 2+2?")

    @patch("app.services.education_service.parse_json_from_llm")
    def test_recommend_endpoint(self, mock_parse_json):
        """Verifies POST /recommend creates personalized roadmaps."""
        mock_roadmap_data = {
            "roadmap": [
                {
                    "phase": "Phase 1",
                    "title": "Learn HTML",
                    "description": "Structure web docs",
                    "duration": "2 days"
                }
            ],
            "resources": [
                {
                    "name": "MDN Web Docs",
                    "type": "Article",
                    "description": "Standard guide reference"
                }
            ],
            "practice_suggestions": ["Build a home page layout"]
        }
        mock_parse_json.return_value = mock_roadmap_data

        payload = {
            "topic": "Frontend Development",
            "skill_level": "Beginner",
            "goals": "Build personal website portfolios",
            "model_preference": "gemini"
        }
        response = client.post("/recommend", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["topic"], "Frontend Development")
        self.assertEqual(data["skill_level"], "Beginner")
        self.assertEqual(len(data["roadmap"]), 1)
        self.assertEqual(data["roadmap"][0]["title"], "Learn HTML")
        self.assertEqual(len(data["resources"]), 1)
        self.assertEqual(data["practice_suggestions"][0], "Build a home page layout")

if __name__ == "__main__":
    unittest.main()
