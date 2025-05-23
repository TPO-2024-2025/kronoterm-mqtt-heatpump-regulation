import pytest
from unittest.mock import patch

SERVICE_SET_VALUE = "set_value"

from custom_components.kronoterm_integration import DOMAIN
from custom_components.kronoterm_integration.number import KronotermNumber


@pytest.mark.asyncio
async def test_number_publishes_mqtt(hass):
    # Patch MQTT publish so no real MQTT is used
    with patch("homeassistant.components.mqtt.publish") as mock_publish:
        # Set up the real number entity
        entity = KronotermNumber(
            name="Dummy Number 1",
            topic="homeassistant/number/kronoterm/kronoterm-dummy_number_1/command",
            min_value=0,
            max_value=100,
            step=1,
            native_unit_of_measurement="°C",
        )
        entity.hass = hass

        # Provide fake number entity loader in hass.data
        class DummyLoader:
            numbers = [{"entity": entity}]

        hass.data.setdefault(DOMAIN, {})["kronoterm_sensor_loader"] = DummyLoader()

        # Set up config entry to ensure entity setup
        await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        await hass.async_block_till_done()

        entity_id = "number.dummy_number_1"
        topic = "homeassistant/number/kronoterm/kronoterm-dummy_number_1/command"
        value = 42.0

        # Call the number.set_value service
        await hass.services.async_call(
            "number",
            SERVICE_SET_VALUE,
            {"entity_id": entity_id, "value": value},
            blocking=True,
        )

        # Assert that MQTT was published with expected parameters
        mock_publish.assert_any_call(hass, topic, str(value))
