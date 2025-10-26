"""
Pytest configuration and fixtures for testing.
"""
import os
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from httpx import AsyncClient

from server.app.database import get_db, Base
from server.app.main import app
from server.app.models.user import User, UserStatusEnum
from server.app.models.payment import Plan, Subscription, Payment, Invoice, Coupon
from server.app.core.security import hash_password, JWTManager
from server.app.services.user_service import UserService
from server.app.services.payment_service import PaymentService
from server.app.services.audit_service import AuditService
from server.app.services.admin_service import AdminService


# Test database URL (SQLite in memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def override_get_db(db_session):
    """Override the get_db dependency."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(override_get_db) -> Generator[TestClient, None, None]:
    """Create a test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function")
def user_service(db_session):
    """Create UserService instance."""
    return UserService()


@pytest.fixture(scope="function")
def payment_service(db_session):
    """Create PaymentService instance."""
    return PaymentService(db_session)


@pytest.fixture(scope="function")
def audit_service(db_session):
    """Create AuditService instance."""
    return AuditService(db_session)


@pytest.fixture(scope="function")
def admin_service(db_session):
    """Create AdminService instance."""
    return AdminService(db_session)


@pytest.fixture(scope="function")
def test_user(db_session) -> User:
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("testpassword"),
        nickname="Test User",
        status=UserStatusEnum.ACTIVE,
        email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_user(db_session) -> User:
    """Create an admin user."""
    user = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("adminpassword"),
        nickname="Admin User",
        status=UserStatusEnum.ACTIVE,
        email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_plan(db_session) -> Plan:
    """Create a test plan."""
    plan = Plan(
        name="Basic Plan",
        description="Basic subscription plan",
        price=9.99,
        duration_months=1,
        features={"max_streams": 5, "ai_analysis": True}
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    return plan


@pytest.fixture(scope="function")
def test_coupon(db_session) -> Coupon:
    """Create a test coupon."""
    coupon = Coupon(
        code="TEST10",
        discount_type="percentage",
        discount_value=10.0,
        usage_limit=100,
        is_active=True
    )
    db_session.add(coupon)
    db_session.commit()
    db_session.refresh(coupon)
    return coupon


@pytest.fixture(scope="function")
def user_token(test_user) -> str:
    """Create access token for test user."""
    return JWTManager.create_access_token(data={"sub": test_user.username})


@pytest.fixture(scope="function")
def admin_token(admin_user) -> str:
    """Create access token for admin user."""
    return JWTManager.create_access_token(data={"sub": admin_user.username})


@pytest.fixture(scope="function")
def auth_headers(user_token) -> dict:
    """Create authorization headers for test user."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture(scope="function")
def admin_headers(admin_token) -> dict:
    """Create authorization headers for admin user."""
    return {"Authorization": f"Bearer {admin_token}"}


# Test data fixtures
@pytest.fixture
def sample_user_data():
    """Sample user registration data."""
    return {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "newpassword123",
        "full_name": "New User"
    }


@pytest.fixture
def sample_plan_data():
    """Sample plan creation data."""
    return {
        "name": "Premium Plan",
        "description": "Premium subscription with all features",
        "price": 19.99,
        "duration_months": 1,
        "features": {
            "max_streams": 20,
            "ai_analysis": True,
            "priority_support": True
        }
    }


@pytest.fixture
def sample_payment_data():
    """Sample payment data."""
    return {
        "amount": 9.99,
        "payment_method": "credit_card",
        "currency": "USD"
    }


# Environment setup
@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables."""
    os.environ["TESTING"] = "1"
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["DATABASE_URL"] = SQLALCHEMY_DATABASE_URL
    yield
    # Cleanup
    if "TESTING" in os.environ:
        del os.environ["TESTING"]