from fastapi.testclient import TestClient
from datetime import datetime
from decimal import Decimal
from app.models import Transaction, TransactionType, BankSource, User


DEBIT_TX = {
    "date": "2026-03-15T10:00:00",
    "description": "Compra supermercado Lider",
    "amount": "35000",
    "transaction_type": "debit",
    "bank_source": "santander",
}

CREDIT_TX = {
    "date": "2026-03-01T08:00:00",
    "description": "Abono sueldo",
    "amount": "1500000",
    "transaction_type": "credit",
    "bank_source": "falabella",
}


def test_create_and_get_transaction(client: TestClient):
    resp = client.post("/transactions/", json=DEBIT_TX)
    assert resp.status_code == 201
    tx = resp.json()
    assert tx["description"] == DEBIT_TX["description"]
    assert tx["transaction_type"] == "debit"
    assert tx["bank_source"] == "santander"

    get_resp = client.get(f"/transactions/{tx['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == tx["id"]


def test_list_transactions(client: TestClient):
    client.post("/transactions/", json=DEBIT_TX)
    client.post("/transactions/", json=CREDIT_TX)
    resp = client.get("/transactions/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_filter_by_bank(client: TestClient):
    client.post("/transactions/", json=DEBIT_TX)
    client.post("/transactions/", json=CREDIT_TX)

    resp = client.get("/transactions/?bank=santander")
    assert all(t["bank_source"] == "santander" for t in resp.json())


def test_filter_by_date(client: TestClient):
    client.post("/transactions/", json=DEBIT_TX)
    client.post("/transactions/", json=CREDIT_TX)

    resp = client.get("/transactions/?from_date=2026-03-10T00:00:00")
    dates = [t["date"] for t in resp.json()]
    assert all(d >= "2026-03-10" for d in dates)


def test_update_transaction_category(client: TestClient):
    cat_resp = client.post("/categories/", json={"name": "Supermercado"})
    cat_id = cat_resp.json()["id"]

    tx_resp = client.post("/transactions/", json=DEBIT_TX)
    tx_id = tx_resp.json()["id"]

    resp = client.patch(f"/transactions/{tx_id}", json={"category_id": cat_id})
    assert resp.status_code == 200
    assert resp.json()["category"]["id"] == cat_id


def test_delete_transaction(client: TestClient):
    tx_resp = client.post("/transactions/", json=DEBIT_TX)
    tx_id = tx_resp.json()["id"]

    resp = client.delete(f"/transactions/{tx_id}")
    assert resp.status_code == 204

    get_resp = client.get(f"/transactions/{tx_id}")
    assert get_resp.status_code == 404


def test_get_nonexistent_transaction(client: TestClient):
    resp = client.get("/transactions/9999")
    assert resp.status_code == 404


def test_auto_categorize_on_create(client: TestClient):
    """Transaction should be auto-categorized if description matches a category keyword."""
    client.post("/categories/", json={"name": "Supermercado", "keywords": "supermercado,lider"})
    resp = client.post("/transactions/", json=DEBIT_TX)
    assert resp.status_code == 201
    assert resp.json()["category"]["name"] == "Supermercado"


def test_list_transactions_excludes_other_user_data(client: TestClient, db):
    other_user = User(username="other", hashed_password="x", is_active=True, is_superuser=False)
    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    db.add(
        Transaction(
            user_id=other_user.id,
            date=datetime(2026, 3, 15, 10, 0, 0),
            description="Compra externa",
            amount=Decimal("35000"),
            transaction_type=TransactionType.DEBIT,
            bank_source=BankSource.SANTANDER,
        )
    )
    db.commit()

    resp = client.get("/transactions/")
    assert resp.status_code == 200
    assert resp.json() == []
