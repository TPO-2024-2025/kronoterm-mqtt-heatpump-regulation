from homeassistant.const import Platform

PLATFORMS: list[Platform] = [Platform.SENSOR]

DOMAIN = "kronoterm_integration"

URL_BASE = "/kronoterm_integration"
JSMODULES = [
    {
        "name": "Sensor Data Card",
        "filename": "sensor_data_card.js",
        "version": "1.0.0",
    },
    {
        "name": "Plotly Graph Card",
        "filename": "plotly-graph-card.js",
        "version": "2.0.0",
    },
    {
        "name": "Heatpump Control Card",
        "filename": "heatpump-control-card.js",
        "version": "1.0.0",
    },
]
