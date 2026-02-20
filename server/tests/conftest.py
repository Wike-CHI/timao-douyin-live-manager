"""
Pytest configuration and fixtures for testing.
简化版 - 无用户系统
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

from server.app.database import get_db, get_db_session, Base
from server.app.main import app


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
    app.dependency_overrides[get_db_session] = _override_get_db
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


# ==================== SenseVoice ONNX 测试夹具 ====================

@pytest.fixture
def sample_rate():
    """采样率"""
    return 16000


@pytest.fixture
def test_audio_silence(sample_rate):
    """静音音频 (1秒, 16kHz)"""
    import numpy as np
    duration = 1.0
    samples = int(sample_rate * duration)
    # 全零的 16-bit PCM
    audio = np.zeros(samples, dtype=np.int16)
    return audio.tobytes()


@pytest.fixture
def test_audio_tone(sample_rate):
    """正弦波音频 (1秒, 440Hz)"""
    import numpy as np
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    wave = np.sin(2 * np.pi * 440 * t)
    audio = (wave * 32767 * 0.5).astype(np.int16)
    return audio.tobytes()


@pytest.fixture
def mock_model_dir(tmp_path):
    """模拟模型目录"""
    model_dir = tmp_path / "sherpa-onnx-sense-voice"
    model_dir.mkdir()
    # 创建必要的模型文件
    (model_dir / "model.onnx").touch()
    (model_dir / "tokens.txt").write_text("你好\n世界\n", encoding="utf-8")
    return str(model_dir)
