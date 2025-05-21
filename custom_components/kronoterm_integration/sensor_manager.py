from homeassistant.helpers.area_registry import async_get as async_get_area_registry
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry


class SensorManager:
    _instance = None

    def __init__(self, hass):
        self.hass = hass
        self.sensors = []
        self._sensor_entity = None

    @classmethod
    def get_instance(cls, hass):
        if cls._instance is None:
            cls._instance = cls(hass)
        return cls._instance

    def set_sensor_entity(self, entity):
        self._sensor_entity = entity

    async def _gather_sensors(self):
        entity_registry = async_get_entity_registry(self.hass)
        area_registry = async_get_area_registry(self.hass)

        sensor_list = []
        for domain in ["sensor", "number", "binary_sensor", "switch"]:
            for state in self.hass.states.async_all(domain):
                entry = entity_registry.async_get(state.entity_id)
                area_id = entry.area_id if entry else None
                area_name = None

                if area_id:
                    area_entry = area_registry.async_get_area(area_id)

                    if area_entry:
                        area_name = area_entry.name

                sensor_list.append(
                    {
                        "entity_id": state.entity_id,
                        "name": state.name,
                        "state": state.state,
                        "unit": state.attributes.get("unit_of_measurement"),
                        "area": area_name,
                        "type": state.attributes.get("sensor_type")
                        or state.attributes.get("device_class")
                        or state.domain,
                        "kronoterm": state.attributes.get("kronoterm", False),
                    }
                )

        return sensor_list

    async def get_all_sensors(self) -> list[dict]:
        return await self._gather_sensors()

    async def refresh_sensor_list(self):
        self.sensors = await self._gather_sensors()
        if self._sensor_entity:
            self._sensor_entity.update_sensors(self.sensors)
