import pytest
from unittest.mock import patch
from homeassistant.const import SERVICE_TURN_ON
from custom_components.kronoterm_integration import DOMAIN
from custom_components.kronoterm_integration.switch import KronotermSwitch

# creates a switch entity
# simulates turning on the switch
# checks the MQTT for "on" outgoing


@pytest.mark.asyncio
async def test_switch_publishes_mqtt(hass):
    # Patch MQTT async_publish so no real MQTT is used
    with patch("homeassistant.components.mqtt.async_publish") as mock_async_publish:
        # Set up the real switch entity
        entity = KronotermSwitch(
            name="DHW Circulation Switch",
            topic="homeassistant/switch/kronoterm/kronoterm-dhw_circulation_switch/command",
        )
        entity.hass = hass

        # Provide fake switch entity loader in hass.data
        class DummyLoader:
            switches = [{"entity": entity}]

        hass.data.setdefault(DOMAIN, {})["kronoterm_sensor_loader"] = DummyLoader()

        # Set up config entry to ensure entity setup
        await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        await hass.async_block_till_done()

        entity_id = "switch.dhw_circulation_switch"
        topic = (
            "homeassistant/switch/kronoterm/kronoterm-dhw_circulation_switch/command"
        )

        # Call the service to turn on the switch
        await hass.services.async_call(
            "switch",
            SERVICE_TURN_ON,
            {"entity_id": entity_id},
            blocking=True,
        )

        # Assert that MQTT was published with expected parameters
        mock_async_publish.assert_any_call(hass, topic, "ON")
