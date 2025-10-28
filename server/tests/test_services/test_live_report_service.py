import pytest

from server.app.services.live_report_service import LiveReportService, LiveReportStatus


@pytest.mark.asyncio
async def test_stop_without_session_returns_placeholder(tmp_path):
    service = LiveReportService(records_root=str(tmp_path))

    status = await service.stop()

    assert isinstance(status, LiveReportStatus)
    assert status.session_id == "no-session"
    assert status.room_id is None
    assert status.live_url == ""
