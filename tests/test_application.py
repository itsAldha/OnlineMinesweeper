import pytest
from main.application import application

@pytest.fixture
def client():
    return application.test_client()

def test_response(client):
    result = client.get()
