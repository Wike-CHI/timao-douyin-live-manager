import io
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import service_launcher
from service_launcher import ServiceManager


class DummyProcess:
    """Lightweight stand-in for subprocess.Popen return value."""

    _pid_counter = 1000

    def __init__(self):
        type(self)._pid_counter += 1
        self.pid = type(self)._pid_counter
        self._returncode = None
        self.stdout = io.StringIO("")
        self.stderr = io.StringIO("")

    def poll(self):
        return self._returncode

    @property
    def returncode(self):
        return self._returncode

    def wait(self, timeout=None):
        self._returncode = 0
        return self._returncode

    def terminate(self):
        self._returncode = 0

    def kill(self):
        self._returncode = -9


@pytest.fixture
def manager(monkeypatch):
    mgr = ServiceManager()
    # Avoid spinning up background monitors in unit tests
    monkeypatch.setattr(mgr, "start_health_monitor", lambda: None)
    monkeypatch.setattr(service_launcher.time, "sleep", lambda *_: None)
    return mgr


def test_start_all_services_launches_expected_backends(manager, monkeypatch):
    calls = []

    def fake_start_service(self, name, cmd, cwd=None, expected_port=None):
        calls.append(
            SimpleNamespace(name=name, cmd=list(cmd), cwd=cwd, expected_port=expected_port)
        )
        self.services[name] = DummyProcess()
        return True

    monkeypatch.setattr(ServiceManager, "start_service", fake_start_service, raising=False)

    manager.start_all_services()

    assert [call.name for call in calls[:2]] == ["fastapi_main", "streamcap"]
    fastapi_call, streamcap_call = calls[:2]

    assert fastapi_call.cmd == [
        service_launcher.sys.executable,
        "-m",
        "uvicorn",
        "server.app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "9019",
        "--log-level",
        "info",
    ]
    assert fastapi_call.cwd == manager.base_dir
    assert fastapi_call.expected_port == 9019

    assert streamcap_call.cmd[-2:] == ["--port", "6006"]
    assert streamcap_call.cwd == manager.base_dir / "StreamCap"
    assert streamcap_call.expected_port == 6006

    status = manager.get_service_status()
    assert status["fastapi_main"]["running"]
    assert status["streamcap"]["running"]

    manager.stop_all_services()


def test_start_service_reassigns_port_when_conflict(manager, monkeypatch):
    monkeypatch.setattr(ServiceManager, "is_port_in_use", lambda self, port: True)
    monkeypatch.setattr(ServiceManager, "find_free_port", lambda self, _: 9020)
    monkeypatch.setattr(manager, "start_output_monitor", lambda *args, **kwargs: None)

    captured = {}

    def fake_popen(cmd, **kwargs):
        captured["cmd"] = list(cmd)
        captured["cwd"] = kwargs.get("cwd")
        return DummyProcess()

    monkeypatch.setattr(service_launcher.subprocess, "Popen", fake_popen)

    result = manager.start_service(
        "fastapi_main",
        [
            service_launcher.sys.executable,
            "-m",
            "uvicorn",
            "server.app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "9019",
            "--log-level",
            "info",
        ],
        cwd=str(manager.base_dir),
        expected_port=9019,
    )

    assert result is True
    assert "fastapi_main" in manager.services
    assert "9019" not in captured["cmd"]
    assert "9020" in captured["cmd"]

    manager.stop_all_services()
