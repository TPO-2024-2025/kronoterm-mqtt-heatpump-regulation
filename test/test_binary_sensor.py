"""Binary sensor tests."""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.kronoterm_integration import DOMAIN
from custom_components.kronoterm_integration.binary_sensor import KronotermBinarySensor


@pytest.mark.asyncio
async def test_turn_on(hass: HomeAssistant) -> None:
    """Test turning on binary sensor."""
    await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})

    ksl = hass.data[DOMAIN]["kronoterm_sensor_loader"]
    sensor_defs = ksl.binary_sensors
    sensor: KronotermBinarySensor = sensor_defs[0]["entity"]

    sensor._msg_received("ON")
    assert sensor.is_on


@pytest.mark.asyncio
async def test_turn_off(hass: HomeAssistant) -> None:
    """Test turning off binary sensor."""
    await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})

    ksl = hass.data[DOMAIN]["kronoterm_sensor_loader"]
    sensor_defs = ksl.binary_sensors
    sensor: KronotermBinarySensor = sensor_defs[0]["entity"]

    sensor._msg_received("OFF")
    assert not sensor.is_on
