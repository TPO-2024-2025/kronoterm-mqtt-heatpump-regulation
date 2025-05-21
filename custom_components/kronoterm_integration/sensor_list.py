from homeassistant.helpers.entity import Entity


class KronotermSensorListEntity(Entity):
    def __init__(self, hass):
        super().__init__()
        self._attr_name = "Kronoterm Sensor List"
        self._attr_unique_id = "kronoterm_sensor_list"
        self._attr_icon = "mdi:format-list-bulleted"
        self._state = "ready"
        self._sensors = []

    def update_sensors(self, sensors):
        self._sensors = sensors
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        sensors_info = []

        for s in self._sensors:
            state_obj = self.hass.states.get(s["entity_id"])
            if not state_obj:
                continue

            enriched_sensor = {
                "id": s["entity_id"],
                "name": s.get("name"),
                "area": s.get("area"),
                "state": state_obj.state,
                "unit": s.get("unit"),
                "last_updated": state_obj.last_updated.isoformat()
                if state_obj.last_updated
                else None,
                "available": state_obj.state != "unavailable",
                "kronoterm": s.get("kronoterm", False),
            }

            sensors_info.append(enriched_sensor)

        return {"sensors": sensors_info}
