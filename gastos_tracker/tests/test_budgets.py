from fastapi.testclient import TestClient
from app.models import Budget, Category, User


def _create_category(client: TestClient, name: str = "Comida") -> int:
    resp = client.post("/categories/", json={"name": name})
    return resp.json()["id"]


def test_create_budget(client: TestClient):
    cat_id = _create_category(client)
    resp = client.post("/budgets/", json={"category_id": cat_id, "monthly_limit": "200000", "alert_threshold": 0.8})
    assert resp.status_code == 201
    data = resp.json()
    assert float(data["monthly_limit"]) == 200000.0
    assert data["alert_threshold"] == 0.8


def test_duplicate_budget_for_same_category(client: TestClient):
    cat_id = _create_category(client)
    client.post("/budgets/", json={"category_id": cat_id, "monthly_limit": "100000"})
    resp = client.post("/budgets/", json={"category_id": cat_id, "monthly_limit": "200000"})
    assert resp.status_code == 409


def test_update_budget(client: TestClient):
    cat_id = _create_category(client)
    create_resp = client.post("/budgets/", json={"category_id": cat_id, "monthly_limit": "100000"})
    budget_id = create_resp.json()["id"]

    resp = client.patch(f"/budgets/{budget_id}", json={"monthly_limit": "150000"})
    assert resp.status_code == 200
    assert float(resp.json()["monthly_limit"]) == 150000.0


def test_delete_budget(client: TestClient):
    cat_id = _create_category(client)
    create_resp = client.post("/budgets/", json={"category_id": cat_id, "monthly_limit": "100000"})
    budget_id = create_resp.json()["id"]

    resp = client.delete(f"/budgets/{budget_id}")
    assert resp.status_code == 204


def test_budget_alerts_no_spending(client: TestClient):
    cat_id = _create_category(client)
    client.post("/budgets/", json={"category_id": cat_id, "monthly_limit": "100000", "alert_threshold": 0.8})

    resp = client.get("/budgets/alerts/current")
    assert resp.status_code == 200
    # No transactions yet → no alerts
    assert resp.json() == []


def test_budget_alert_triggered(client: TestClient):
    """Spending >= alert_threshold should appear in alerts."""
    cat_id = _create_category(client, "Transporte")
    client.post("/budgets/", json={"category_id": cat_id, "monthly_limit": "100000", "alert_threshold": 0.5})

    # Spend 60% of budget
    import datetime
    this_month = datetime.datetime.now().replace(day=10).isoformat()
    client.post("/transactions/", json={
        "date": this_month,
        "description": "Uber ride",
        "amount": "60000",
        "transaction_type": "debit",
        "bank_source": "manual",
        "category_id": cat_id,
    })

    resp = client.get("/budgets/alerts/current")
    assert resp.status_code == 200
    alerts = resp.json()
    assert len(alerts) == 1
    assert alerts[0]["category_name"] == "Transporte"
    assert alerts[0]["percentage_used"] == 60.0
    assert alerts[0]["is_exceeded"] is False


def test_list_budgets_excludes_other_user_data(client: TestClient, db):
    other_user = User(username="other", hashed_password="x", is_active=True, is_superuser=False)
    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    category = Category(user_id=other_user.id, name="Privada")
    db.add(category)
    db.commit()
    db.refresh(category)

    db.add(Budget(user_id=other_user.id, category_id=category.id, monthly_limit="100000", alert_threshold=0.8))
    db.commit()

    resp = client.get("/budgets/")
    assert resp.status_code == 200
    assert resp.json() == []
