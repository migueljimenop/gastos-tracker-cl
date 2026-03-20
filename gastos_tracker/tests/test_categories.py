import pytest
from fastapi.testclient import TestClient


def test_list_categories_empty(client: TestClient):
    response = client.get("/categories/")
    assert response.status_code == 200
    assert response.json() == []


def test_create_category(client: TestClient):
    payload = {"name": "Comida", "keywords": "supermercado,restaurant,delivery", "color": "#f59e0b"}
    response = client.post("/categories/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Comida"
    assert data["keywords"] == "supermercado,restaurant,delivery"
    assert data["id"] is not None


def test_create_duplicate_category(client: TestClient):
    payload = {"name": "Transporte"}
    client.post("/categories/", json=payload)
    response = client.post("/categories/", json=payload)
    assert response.status_code == 409


def test_update_category(client: TestClient):
    create_resp = client.post("/categories/", json={"name": "Entretenimiento"})
    cat_id = create_resp.json()["id"]

    response = client.patch(f"/categories/{cat_id}", json={"keywords": "cine,netflix,spotify"})
    assert response.status_code == 200
    assert response.json()["keywords"] == "cine,netflix,spotify"


def test_update_nonexistent_category(client: TestClient):
    response = client.patch("/categories/9999", json={"name": "X"})
    assert response.status_code == 404


def test_delete_category(client: TestClient):
    create_resp = client.post("/categories/", json={"name": "Temporal"})
    cat_id = create_resp.json()["id"]

    response = client.delete(f"/categories/{cat_id}")
    assert response.status_code == 204

    list_resp = client.get("/categories/")
    assert all(c["id"] != cat_id for c in list_resp.json())


def test_delete_nonexistent_category(client: TestClient):
    response = client.delete("/categories/9999")
    assert response.status_code == 404
