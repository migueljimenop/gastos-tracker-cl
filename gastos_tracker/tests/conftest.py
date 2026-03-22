import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.dependencies import get_current_superuser, get_current_user
from app.main import app
from app.models import User

TEST_DATABASE_URL = "sqlite:///./test_gastos.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def _mock_user():
    return User(id=1, username="testuser", hashed_password="x", is_active=True, is_superuser=False)


@pytest.fixture
def client(db):
    if not db.get(User, 1):
        db.add(_mock_user())
        db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    def override_current_user():
        return db.get(User, 1)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(db):
    admin = db.query(User).filter(User.username == "admin-test").first()
    if not admin:
        admin = User(username="admin-test", hashed_password="x", is_active=True, is_superuser=True)
        db.add(admin)
        db.commit()
        db.refresh(admin)

    def override_get_db():
        try:
            yield db
        finally:
            pass

    def override_current_user():
        return admin

    def override_current_superuser():
        return admin

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_current_superuser] = override_current_superuser
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
