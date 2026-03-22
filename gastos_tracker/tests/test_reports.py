import datetime
from fastapi.testclient import TestClient


def _post_tx(client: TestClient, description: str, amount: str, tx_type: str, day: int = 15, cat_id: int | None = None):
    payload = {
        "date": datetime.datetime(2026, 3, day).isoformat(),
        "description": description,
        "amount": amount,
        "transaction_type": tx_type,
        "bank_source": "santander",
    }
    if cat_id:
        payload["category_id"] = cat_id
    return client.post("/transactions/", json=payload)


def test_monthly_report_empty(client: TestClient):
    resp = client.get("/reports/monthly?year=2026&month=3")
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["total_spent"]) == 0.0
    assert float(data["total_income"]) == 0.0
    assert data["by_category"] == []


def test_monthly_report_with_data(client: TestClient):
    cat_resp = client.post("/categories/", json={"name": "Comida"})
    cat_id = cat_resp.json()["id"]

    _post_tx(client, "Supermercado", "50000", "debit", cat_id=cat_id)
    _post_tx(client, "Restaurant", "20000", "debit", cat_id=cat_id)
    _post_tx(client, "Sueldo", "1000000", "credit")

    resp = client.get("/reports/monthly?year=2026&month=3")
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["total_spent"]) == 70000.0
    assert float(data["total_income"]) == 1000000.0
    assert len(data["by_category"]) == 1
    assert data["by_category"][0]["category_name"] == "Comida"
    assert data["by_category"][0]["count"] == 2


def test_monthly_report_uncategorized(client: TestClient):
    _post_tx(client, "Gasto varios", "15000", "debit")

    resp = client.get("/reports/monthly?year=2026&month=3")
    data = resp.json()
    assert data["by_category"][0]["category_name"] == "Sin categoría"


def test_export_csv(client: TestClient):
    _post_tx(client, "Compra online", "30000", "debit")
    resp = client.get("/reports/export/csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "Compra online" in resp.text


def test_export_excel(client: TestClient):
    _post_tx(client, "Compra online", "30000", "debit")
    resp = client.get("/reports/export/excel")
    assert resp.status_code == 200
    # Excel files start with PK (ZIP magic bytes)
    assert resp.content[:2] == b"PK"


def test_export_csv_empty(client: TestClient):
    resp = client.get("/reports/export/csv")
    assert resp.status_code == 200
    assert resp.text == ""
