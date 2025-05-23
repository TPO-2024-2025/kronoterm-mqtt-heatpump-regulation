import pytest
from unittest.mock import Mock, patch

from custom_components.kronoterm_integration.sensor_manager import SensorManager


@pytest.mark.asyncio
async def test_gather_sensors_with_areas(hass):
    # -- Dummy State object, mimics homeassistant.core.State --
    class DummyState:
        def __init__(self, entity_id, name, state, attrs, domain):
            self.entity_id = entity_id
            self.name = name
            self.state = state
            self.attributes = attrs
            self.domain = domain

    # -- Fake list of states, for each domain --
    dummy_states = [
        DummyState(
            "sensor.foo",
            "Foo Sensor",
            "42",
            {"unit_of_measurement": "°C", "sensor_type": "number", "kronoterm": True},
            "sensor",
        ),
        DummyState(
            "number.bar",
            "Bar Number",
            "10",
            {"unit_of_measurement": "°C", "device_class": "temperature"},
            "number",
        ),
        DummyState("switch.baz", "Baz Switch", "on", {}, "switch"),
        DummyState("binary_sensor.qux", "Qux Binary", "off", {}, "binary_sensor"),
    ]

    # -- Patch the registries normally --
    dummy_entity_entry = Mock()
    dummy_entity_entry.area_id = "area_1"
    dummy_area_entry = Mock()
    dummy_area_entry.name = "Living Room"

    fake_entity_registry = Mock()
    fake_entity_registry.async_get.return_value = dummy_entity_entry
    fake_area_registry = Mock()
    fake_area_registry.async_get_area.return_value = dummy_area_entry

    # --- Here's the important trick! ---
    # Create a dummy "states" with an async_all method
    class DummyStates:
        def async_all(self, domain):
            return [s for s in dummy_states if s.domain == domain]

    # Patch hass.states (not the method) to our DummyStates instance
    old_states = hass.states
    hass.states = DummyStates()

    try:
        # Patch registries
        with (
            patch(
                "custom_components.kronoterm_integration.sensor_manager.async_get_entity_registry",
                return_value=fake_entity_registry,
            ),
            patch(
                "custom_components.kronoterm_integration.sensor_manager.async_get_area_registry",
                return_value=fake_area_registry,
            ),
        ):
            mgr = SensorManager(hass)
            result = await mgr._gather_sensors()
    finally:
        # Restore the original states to avoid side-effects
        hass.states = old_states

    # -- Now, assert your result as usual --
    # -- Now, assert your result as usual --

    expected_ids = {"sensor.foo", "number.bar", "switch.baz", "binary_sensor.qux"}
    actual_ids = {s["entity_id"] for s in result}
    assert actual_ids == expected_ids

    for s in result:
        if s["entity_id"] in ("sensor.foo", "number.bar"):
            assert s["area"] == "Living Room"
