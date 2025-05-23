import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import json

from custom_components.kronoterm_integration.history_storage import SensorHistoryView


@pytest.fixture
def hass():
    mock_hass = Mock()
    mock_hass.async_add_executor_job = lambda func: func()
    return mock_hass


def make_request(params):
    req = Mock()
    req.query = params
    return req


@pytest.mark.asyncio
async def test_missing_sensor_param(hass):
    view = SensorHistoryView(hass)
    request = make_request({})
    resp = await view.get(request)
    assert resp.status == 400
    assert "Missing sensor parameter" in resp.body.decode()


@pytest.mark.asyncio
async def test_invalid_hours_param(hass):
    view = SensorHistoryView(hass)
    request = make_request({"sensor": "sensor.foo", "hours": "abc"})
    resp = await view.get(request)
    assert resp.status == 400
    assert "Invalid 'hours' parameter" in resp.body.decode()


@pytest.mark.asyncio
async def test_history_json(hass):
    now = datetime.now(timezone.utc)
    mock_state = Mock()
    mock_state.last_updated = now
    mock_state.state = "23"
    with (
        patch(
            "custom_components.kronoterm_integration.history_storage.get_instance"
        ) as mock_get_instance,
        patch(
            "custom_components.kronoterm_integration.history_storage.state_changes_during_period"
        ) as mock_state_changes,
        patch.object(hass, "async_add_executor_job") as mock_async_job,
    ):
        mock_recorder = MagicMock()
        mock_get_instance.return_value = mock_recorder
        mock_session = MagicMock()
        mock_recorder.get_session.return_value = mock_session
        mock_session.__enter__.return_value = None
        mock_session.__exit__.return_value = False
        mock_state_changes.return_value = {"sensor.foo": [mock_state]}

        # Correct: async def
        async def fake_async_add_executor_job(func, *args, **kwargs):
            return func(*args, **kwargs)

        mock_async_job.side_effect = fake_async_add_executor_job

        view = SensorHistoryView(hass)
        request = make_request({"sensor": "sensor.foo", "hours": "2"})
        result = await view.get(request)
        body = result.body.decode()
        json_result = json.loads(body)
        assert "sensor.foo" in json_result
        assert json_result["sensor.foo"][0]["state"] == "23"


@pytest.mark.asyncio
async def test_history_csv(hass):
    now = datetime.now(timezone.utc)
    mock_state = Mock()
    mock_state.last_updated = now
    mock_state.state = "42"
    with (
        patch(
            "custom_components.kronoterm_integration.history_storage.get_instance"
        ) as mock_get_instance,
        patch(
            "custom_components.kronoterm_integration.history_storage.state_changes_during_period"
        ) as mock_state_changes,
        patch.object(hass, "async_add_executor_job") as mock_async_job,
    ):
        mock_recorder = MagicMock()
        mock_get_instance.return_value = mock_recorder
        mock_session = MagicMock()
        mock_recorder.get_session.return_value = mock_session
        mock_session.__enter__.return_value = None
        mock_session.__exit__.return_value = False
        mock_state_changes.return_value = {"sensor.foo": [mock_state]}

        async def fake_async_add_executor_job(func, *args, **kwargs):
            return func(*args, **kwargs)

        mock_async_job.side_effect = fake_async_add_executor_job

        view = SensorHistoryView(hass)
        request = make_request({"sensor": "sensor.foo", "format": "csv"})
        result = await view.get(request)
        body = result.body.decode()
        assert "timestamp,state" in body
        assert ",42" in body


@pytest.mark.asyncio
async def test_history_exception(hass):
    with patch(
        "custom_components.kronoterm_integration.history_storage.get_instance"
    ) as mock_get_instance:
        mock_get_instance.side_effect = Exception("No recorder")
        view = SensorHistoryView(hass)
        request = make_request({"sensor": "sensor.foo"})
        try:
            await view.get(request)
        except Exception as exc:
            assert "No recorder" in str(exc)
