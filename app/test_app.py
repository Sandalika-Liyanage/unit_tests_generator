import pytest
from fastapi.testclient import TestClient
from main import app
from datetime import date

client = TestClient(app)


def test_root():
    """
    Test the root endpoint by sending a GET request to "/" and checking the response status code and JSON body.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_echo_endpoint_valid_input():
    """
    Test the /echo endpoint with a valid JSON body.
    """
    response = client.post("/echo", json={"key": "value"})
    assert response.status_code == 200
    assert response.json() == {"you_sent": {"key": "value"}}


def test_add_endpoint_valid_input():
    """
    Test the /add endpoint with valid integer inputs.
    """
    response = client.get("/add?a=3&b=5")
    assert response.status_code == 200
    assert response.json() == {"result": 8}
