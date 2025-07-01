import pytest
from app.calculator import Calculator
from app.main import app
from fastapi.testclient import TestClient

# Initialize test client for FastAPI
client = TestClient(app)

class TestCalculator:
    def test_add(self):
        assert 1==1


