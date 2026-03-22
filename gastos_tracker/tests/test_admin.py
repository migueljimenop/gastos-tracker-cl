from fastapi.testclient import TestClient

from app.models import AuditLog


def test_audit_logs_requires_superuser(client: TestClient):
    response = client.get("/admin/audit-logs")

    assert response.status_code == 403


def test_superuser_can_list_audit_logs(admin_client: TestClient, db):
    db.add(
        AuditLog(
            user_id=1,
            action="transaction.created",
            entity_type="transaction",
            entity_id=10,
            details="{}",
        )
    )
    db.commit()

    response = admin_client.get("/admin/audit-logs")

    assert response.status_code == 200
    payload = response.json()
    assert any(item["action"] == "transaction.created" for item in payload)


def test_superuser_can_filter_audit_logs(admin_client: TestClient, db):
    db.add_all(
        [
            AuditLog(user_id=1, action="transaction.created", entity_type="transaction", entity_id=1, details="{}"),
            AuditLog(user_id=1, action="budget.created", entity_type="budget", entity_id=2, details="{}"),
        ]
    )
    db.commit()

    response = admin_client.get("/admin/audit-logs?action=budget.created&entity_type=budget")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["action"] == "budget.created"


def test_audit_log_query_is_itself_audited(admin_client: TestClient, db):
    response = admin_client.get("/admin/audit-logs")

    assert response.status_code == 200
    entry = db.query(AuditLog).filter(AuditLog.action == "audit.viewed").order_by(AuditLog.id.desc()).first()
    assert entry is not None