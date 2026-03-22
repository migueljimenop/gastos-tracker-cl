import json

from fastapi.testclient import TestClient

from app.models import AuditLog


def _latest_log(db, action: str) -> AuditLog:
    return db.query(AuditLog).filter(AuditLog.action == action).order_by(AuditLog.id.desc()).first()


def test_category_crud_creates_audit_logs(client: TestClient, db):
    create_resp = client.post("/categories/", json={"name": "Auditoria"})
    category_id = create_resp.json()["id"]

    client.patch(f"/categories/{category_id}", json={"keywords": "log"})
    client.delete(f"/categories/{category_id}")

    created = _latest_log(db, "category.created")
    updated = _latest_log(db, "category.updated")
    deleted = _latest_log(db, "category.deleted")

    assert created is not None
    assert created.entity_type == "category"
    assert created.user_id == 1
    assert created.entity_id == category_id

    assert updated is not None
    assert json.loads(updated.details)["changed_fields"] == ["keywords"]

    assert deleted is not None
    assert deleted.entity_id == category_id


def test_transaction_crud_creates_audit_logs(client: TestClient, db):
    create_resp = client.post(
        "/transactions/",
        json={
            "date": "2026-03-15T10:00:00",
            "description": "Compra auditada",
            "amount": "35000",
            "transaction_type": "debit",
            "bank_source": "manual",
        },
    )
    tx_id = create_resp.json()["id"]

    client.patch(f"/transactions/{tx_id}", json={"notes": "auditado"})
    client.delete(f"/transactions/{tx_id}")

    created = _latest_log(db, "transaction.created")
    updated = _latest_log(db, "transaction.updated")
    deleted = _latest_log(db, "transaction.deleted")

    assert created is not None
    assert created.entity_id == tx_id
    assert json.loads(created.details)["bank_source"] == "manual"

    assert updated is not None
    assert json.loads(updated.details)["changed_fields"] == ["notes"]

    assert deleted is not None
    assert json.loads(deleted.details)["bulk"] is False


def test_budget_and_export_create_audit_logs(client: TestClient, db):
    category_id = client.post("/categories/", json={"name": "Presupuesto Audit"}).json()["id"]
    budget_resp = client.post(
        "/budgets/",
        json={"category_id": category_id, "monthly_limit": "100000", "alert_threshold": 0.8},
    )
    budget_id = budget_resp.json()["id"]

    client.patch(f"/budgets/{budget_id}", json={"monthly_limit": "150000"})
    client.get("/reports/export/csv")

    created = _latest_log(db, "budget.created")
    updated = _latest_log(db, "budget.updated")
    exported = _latest_log(db, "report.exported_csv")

    assert created is not None
    assert created.entity_id == budget_id
    assert updated is not None
    assert json.loads(updated.details)["changed_fields"] == ["monthly_limit"]
    assert exported is not None
    assert exported.entity_type == "report"