from datetime import datetime, timedelta

from aiohttp.web_response import Response
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.history import state_changes_during_period
from homeassistant.core import HomeAssistant


class SensorHistoryView(HomeAssistantView):
    url = "/api/kronoterm_integration/history"
    name = "api:kronoterm_integration:history"
    requires_auth = True

    def __init__(self, hass: HomeAssistant):
        self.hass = hass

    async def get(self, request):
        sensor_id = request.query.get("sensor")
        export_csv = request.query.get("format") == "csv"

        if not sensor_id:
            return self.json_message("Missing sensor parameter", status_code=400)

        try:
            hours = int(request.query.get("hours", 6))
        except ValueError:
            return self.json_message("Invalid 'hours' parameter", status_code=400)

        now = datetime.utcnow()
        start_time = now - timedelta(hours=hours)

        instance = get_instance(self.hass)

        def fetch():
            with instance.get_session() as session:
                return state_changes_during_period(
                    self.hass,
                    start_time,
                    now,
                    entity_id=sensor_id,
                    include_start_time_state=True,
                    no_attributes=False,
                )

        try:
            states = await self.hass.async_add_executor_job(fetch)
        except Exception as e:
            return self.json_message(f"History fetch failed: {e!s}", status_code=500)

        records = []
        for state in states.get(sensor_id, []):
            try:
                records.append(
                    {"timestamp": state.last_updated.isoformat(), "state": state.state}
                )
            except Exception:
                continue

        if export_csv:
            output = "timestamp,state\n" + "\n".join(
                f"{row['timestamp']},{row['state']}" for row in records
            )
            return Response(
                body=output,
                content_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={sensor_id.replace('.', '_')}_history.csv"
                },
            )

        return self.json({sensor_id: records})
