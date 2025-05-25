from __future__ import annotations

import yaml
import logging
from pathlib import Path
from .sensor_list import KronotermSensorListEntity
from homeassistant.components.http import StaticPathConfig

from homeassistant import config_entries
from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .frontend import JSModuleRegistration
from .history_storage import SensorHistoryView
from .kronoterm_sensor_loader import KronotermSensorLoader
from .sensor_manager import SensorManager
from homeassistant.helpers.entity_component import async_update_entity
from homeassistant.helpers.entity_registry import async_get

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    if hass.data.get("lovelace") is not None:
        await JSModuleRegistration(hass).async_register()

    manager = SensorManager.get_instance(hass)

    # Register service to manually refresh sensors
    async def handle_refresh(_call) -> None:
        await manager.refresh_sensor_list()
        _LOGGER.info("Sensor list refreshed by user.")

    hass.services.async_register(
        "kronoterm_integration", "refresh_sensors", handle_refresh
    )

    # Register REST API endpoint for fetching sensor history
    hass.http.register_view(SensorHistoryView(hass))

    kronoterm_sensor_list_entity = KronotermSensorListEntity(hass)
    hass.data.setdefault(DOMAIN, {})["kronoterm_list_entity"] = (
        kronoterm_sensor_list_entity
    )

    loader = KronotermSensorLoader(Path(__file__).parent / "kronoterm_ksm.toml")
    await hass.async_add_executor_job(loader.load)
    hass.data.setdefault(DOMAIN, {})["kronoterm_sensor_loader"] = loader

    # Must be here because MQTT subscriptions happen in sensor setup
    await mqtt.async_wait_for_mqtt_client(hass)

    await hass.config_entries.async_forward_entry_setups(
        entry,
        [
            "sensor",
            "binary_sensor",
            "number",
            "switch",
        ],
    )

    manager.set_sensor_entity(kronoterm_sensor_list_entity)
    await manager.refresh_sensor_list()

    # Step 1: get error_* entities from state machine
    all_entities = hass.states.async_entity_ids()
    error_sensors = sorted(
        [
            eid
            for eid in all_entities
            if eid.startswith("sensor.error_") or eid.startswith("binary_sensor.error_")
        ]
    )

    # Step 2: write dynamic blueprint YAML
    if error_sensors:
        blueprint_path = Path(hass.config.path("www/kronoterm/blueprints"))
        blueprint_path.mkdir(parents=True, exist_ok=True)

        target_file = blueprint_path / "error_notification_blueprint.yaml"
        _LOGGER.info(
            "Writing Kronoterm error blueprint with %d sensors", len(error_sensors)
        )
        error_sensors = [
            eid
            for eid in hass.states.async_entity_ids()
            if eid.startswith("sensor.error_") or eid.startswith("binary_sensor.error_")
        ]

        if error_sensors:
            blueprint = {
                "blueprint": {
                    "name": "Kronoterm Error Notification",
                    "domain": "automation",
                    "description": "Notifies when any error-related sensor changes",
                },
                "trigger": [{"platform": "state", "entity_id": error_sensors}],
                "action": [
                    {
                        "service": "persistent_notification.create",
                        "data": {
                            "title": "Kronoterm Error",
                            "message": "{{ trigger.to_state.name }} changed to {{ trigger.to_state.state }}",
                        },
                    }
                ],
                "mode": "queued",
            }

            blueprint_path = Path(hass.config.path("www/kronoterm/blueprints"))
            blueprint_path.mkdir(parents=True, exist_ok=True)

            blueprint_file = blueprint_path / "error_notification_blueprint.yaml"
            await hass.async_add_executor_job(
                write_blueprint, blueprint_file, blueprint
            )

            from homeassistant.components.http import StaticPathConfig

            await hass.http.async_register_static_paths(
                [
                    StaticPathConfig(
                        "/kronoterm_blueprints",
                        str(blueprint_path),
                        cache_headers=False,
                    )
                ]
            )

        _LOGGER.info(
            "Blueprint served at /kronoterm_blueprints/error_notification_blueprint.yaml"
        )
    else:
        _LOGGER.warning("No error_* sensors found; skipping blueprint generation.")
    return True


def write_blueprint(blueprint_file, blueprint):
    with open(blueprint_file, "w", encoding="utf-8") as f:
        yaml.dump(blueprint, f, allow_unicode=True, sort_keys=False)
