from re import S
import tomllib
from pathlib import Path

from custom_components.kronoterm_integration.switch import KronotermSwitch

from .binary_sensor import KronotermBinarySensor
from .sensor import KronotermEnumSensor, KronotermNumberSensor
from .number import KronotermNumber


class KronotermSensorLoader:
    def __init__(self, toml_path: Path):
        self.toml_path = str(toml_path)
        self.binary_sensors = []
        self.enum_sensors = []
        self.number_sensors = []
        self.switches = []
        self.numbers = []

    def load(self):
        with open(str(self.toml_path), "rb") as f:
            config = tomllib.load(f)

        self._load_binary_sensors(config)
        self._load_enum_sensors(config)
        self._load_number_sensors(config)  # Based on [sensor] with scale/numeric info
        self._load_switches(config)
        self._load_numbers(config)

        return {
            "binary_sensor": self.binary_sensors,
            "enum_sensor": self.enum_sensors,
            "number_sensor": self.number_sensors,
            "switches": self.switches,
            "numbers": self.numbers,
        }

    def _load_binary_sensors(self, config):
        for entry in config.get("binary_sensor", []):
            name = entry["name"]
            sensor_id = self._slugify(name)
            topic = f"homeassistant/binary_sensor/kronoterm/kronoterm-{self._slugify(name)}/state"
            self.binary_sensors.append(
                {"entity": KronotermBinarySensor(name, sensor_id), "topic": topic}
            )

    def _load_enum_sensors(self, config):
        for entry in config.get("enum_sensor", []):
            name = entry["name"]
            sensor_id = self._slugify(name)
            values = []

            # Combine all option tables (some entries may have multiple [[enum_sensor.options]])
            if "options" in entry:
                for option in entry["options"]:
                    values.extend(option["values"])

            topic = (
                f"homeassistant/sensor/kronoterm/kronoterm-{self._slugify(name)}/state"
            )
            self.enum_sensors.append(
                {"entity": KronotermEnumSensor(name, values, sensor_id), "topic": topic}
            )

    def _load_number_sensors(self, config):
        for entry in config.get("sensor", []):
            name = entry["name"]
            sensor_id = self._slugify(name)
            topic = (
                f"homeassistant/sensor/kronoterm/kronoterm-{self._slugify(name)}/state"
            )

            # Very simple rule to distinguish: if scale is numeric, we assume it's a number sensor
            try:
                scale = float(entry.get("scale", 1))
                unit = entry.get("unit_of_measurement", "")
                min_val, max_val = self._guess_range(entry)
                self.number_sensors.append(
                    {
                        "entity": KronotermNumberSensor(
                            name, min_val, max_val, unit, sensor_id
                        ),
                        "topic": topic,
                    }
                )
            except (ValueError, TypeError):
                pass  # Skip non-numeric ones

    def _load_switches(self, config):
        for entry in config.get("switch", []):
            name = entry["name"]
            topic = f"homeassistant/switch/kronoterm/kronoterm-{self._slugify(name)}/command"

            self.switches.append(
                {"entity": KronotermSwitch(name, topic), "topic": topic}
            )

    def _load_numbers(self, config):
        for entry in config.get("number", []):
            name = entry["name"]
            topic = f"homeassistant/sensor/kronoterm/kronoterm-{self._slugify(name)}/command"

            min_value = float(entry.get("min", 0))
            max_value = float(entry.get("max", 100))
            step = float(entry.get("step", 0.5))
            unit = entry.get("unit_of_measurement", "°C")

            self.numbers.append(
                {
                    "entity": KronotermNumber(
                        name, topic, min_value, max_value, step, unit
                    ),
                    "topic": topic,
                }
            )

    def _guess_range(self, entry):
        """Very basic heuristic for range, you can customize this further."""
        unit = entry.get("unit_of_measurement", "")
        if unit == "°C":
            return 0, 100
        if unit == "bar":
            return 0, 10
        if unit == "%":
            return 0, 100
        if unit == "W":
            return 0, 10000
        if unit == "h":
            return 0, 100000
        return 0, 1000

    def _slugify(self, name: str) -> str:
        return name.lower().replace(" - ", "_").replace(" ", "_").replace("/", "_")
