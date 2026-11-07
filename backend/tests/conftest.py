import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.core.security import hash_password, create_access_token

# In-memory SQLite database for test isolation
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session) -> User:
    user = User(
        email="testowner@reqripple.local",
        name="Test Owner",
        password_hash=hash_password("secret123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_user(db: Session) -> User:
    user = User(
        email="second@reqripple.local",
        name="Second User",
        password_hash=hash_password("secret123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def second_auth_headers(second_user: User) -> dict:
    token = create_access_token(second_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_project(db: Session, test_user: User) -> Project:
    project = Project(
        name="Test Project Alpha",
        description="A project for testing ReqRipple.",
        domain="Quality Assurance",
        owner_user_id=test_user.id,
    )
    db.add(project)
    db.flush()

    member = ProjectMember(
        project_id=project.id,
        user_id=test_user.id,
        role="ADMIN",
    )
    db.add(member)
    db.commit()
    db.refresh(project)
    return project
