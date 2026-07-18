import pytest
from app import create_app, db
from app.models.gene import Gene

@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/bc_platform"
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_gene_list_returns_200(client):
    resp = client.get("/genes/")
    assert resp.status_code == 200

def test_gene_search_works(client):
    resp = client.get("/genes/?q=BRCA1")
    assert resp.status_code == 200
    assert b"BRCA1" in resp.data

def test_gene_detail_returns_200(client):
    resp = client.get("/genes/1")
    assert resp.status_code == 200

def test_gene_api_search(client):
    resp = client.get("/genes/api/search?q=TP53")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)

def test_home_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200