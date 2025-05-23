import pytest
from homeassistant.core import HomeAssistant
from custom_components.kronoterm_integration import DOMAIN
from custom_components.kronoterm_integration.binary_sensor import KronotermBinarySensor
from custom_components.kronoterm_integration.sensor import (
    KronotermNumberSensor,
    KronotermEnumSensor,
)


# BINARY SENSOR TESTS
@pytest.mark.asyncio
async def test_turn_on(hass: HomeAssistant):
    """Test turning on binary sensor."""
    await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    ksl = hass.data[DOMAIN]["kronoterm_sensor_loader"]
    sensor_defs = ksl.binary_sensors
    sensor: KronotermBinarySensor = sensor_defs[0]["entity"]
    sensor._msg_received("ON")
    assert sensor.is_on


@pytest.mark.asyncio
async def test_turn_off(hass: HomeAssistant):
    """Test turning off binary sensor."""
    await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    ksl = hass.data[DOMAIN]["kronoterm_sensor_loader"]
    sensor_defs = ksl.binary_sensors
    sensor: KronotermBinarySensor = sensor_defs[0]["entity"]
    sensor._msg_received("OFF")
    assert not sensor.is_on


# NUMBER SENSOR TEST
@pytest.mark.asyncio
async def test_number_sensor_value(hass: HomeAssistant):
    """Test number sensor value is set correctly from MQTT message."""
    await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    ksl = hass.data[DOMAIN]["kronoterm_sensor_loader"]
    sensor: KronotermNumberSensor = ksl.number_sensors[0]["entity"]
    sensor.hass = hass
    sensor.entity_id = "number.test"
    await sensor.async_added_to_hass()
    sensor._msg_received("42.5")
    assert sensor.native_value == 42.5


# ENUM SENSOR TEST
@pytest.mark.asyncio
async def test_enum_sensor_value(hass: HomeAssistant):
    sensor = KronotermEnumSensor("Test Enum", ["COOLING", "HEATING"], "test_enum")
    sensor.hass = hass
    sensor.entity_id = "sensor.test_enum"  # <-- ADD THIS LINE
    await sensor.async_added_to_hass()
    sensor._msg_received("COOLING")
    assert sensor.native_value == "COOLING"
    sensor._msg_received("HEATING")
    assert sensor.native_value == "HEATING"
    sensor._msg_received("INVALID")  # should not update
    assert sensor.native_value == "HEATING"
