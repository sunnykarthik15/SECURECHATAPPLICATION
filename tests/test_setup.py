import pytest
from app import create_app
from config import TestConfig
from extensions import db, socketio

@pytest.fixture
def app():
    """Create and configure an application instance for tests."""
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

def test_app_creation(app):
    """Test that the application initializes in testing mode."""
    assert app is not None
    assert app.config['TESTING'] is True
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'

def test_extensions_initialized(app):
    """Test that SQLAlchemy and SocketIO are initialized."""
    assert 'sqlalchemy' in app.extensions
    assert 'socketio' in app.extensions

def test_health_check(client):
    """Test the /health endpoint returns 200 and expected status."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'RSA-2048 + AES-256-GCM' in data['crypto_standard']

def test_index_route(client):
    """Test the / endpoint returns 200 and running message."""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert 'Secure Chat E2EE Server running.' in data['message']
