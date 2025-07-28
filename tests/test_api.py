import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import date

client = TestClient(app)