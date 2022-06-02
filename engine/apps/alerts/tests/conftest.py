import pytest

from apps.alerts.incident_appearance.templaters import AlertSlackTemplater


@pytest.fixture()
def mock_alert_renderer_render_for(monkeypatch):
    def mock_render_for(*args, **kwargs):
        return "invalid_render_for"

    monkeypatch.setattr(AlertSlackTemplater, "_render_for", mock_render_for)
