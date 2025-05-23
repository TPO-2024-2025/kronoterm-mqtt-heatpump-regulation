import pytest
from datetime import datetime, timezone
from homeassistant.core import HomeAssistant
from homeassistant.components.mqtt.models import ReceiveMessage
from custom_components.kronoterm_integration import DOMAIN
from custom_components.kronoterm_integration.mqtt_subscription import (
    MqttSubscriptionSubject,
)

# subscribe to MQTT
# initialize a sensor
# mock MQTT ingoing message
# check state change for sensor


@pytest.mark.asyncio
async def test_mqtt_flow_for_binary_sensor(hass: HomeAssistant, monkeypatch):
    registered_callbacks = {}

    async def fake_subscribe(hass_, topic, msg_callback, **kwargs):
        registered_callbacks[topic] = msg_callback
        return lambda: registered_callbacks.pop(topic, None)

    monkeypatch.setattr("homeassistant.components.mqtt.async_subscribe", fake_subscribe)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == "create_entry"
    config_entry = result["result"]
    await hass.async_block_till_done()

    ksl = hass.data[DOMAIN]["kronoterm_sensor_loader"]
    sensor_dict = next((s for s in ksl.binary_sensors if "loop_1" in s["topic"]), None)
    assert sensor_dict is not None

    sensor = sensor_dict["entity"]
    sensor_id = "binary_sensor.loop_1_circulation_pump_status"
    sensor.hass = hass
    await sensor.async_added_to_hass()

    hass.states.async_set(sensor_id, "unknown")  # ← Ensure we start from unknown

    topic = "homeassistant/binary_sensor/kronoterm/kronoterm-loop_1_circulation_pump_status/state"
    msg = ReceiveMessage(
        topic=topic,
        payload="ON",
        qos=0,
        retain=False,
        subscribed_topic=topic,
        timestamp=datetime.now(timezone.utc),
    )

    await registered_callbacks[topic](msg)

    # Manually trigger state update
    await sensor.async_update_ha_state()

    await hass.async_block_till_done()

    state = hass.states.get(sensor_id)

    print("Payload received:", msg.payload)
    print("Current state:", state.state)

    assert state is not None
    assert state.state == "on"
