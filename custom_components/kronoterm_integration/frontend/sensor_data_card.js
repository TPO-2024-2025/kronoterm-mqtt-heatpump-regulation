window.customCards = window.customCards || [];
window.customCards.push({
    type: "sensor-data-card",        // Your card's type
    name: "Sensor Data Card",        // Display name in card picker
    preview: true,                   // Optional: enable preview image
    description: "Shows sensor values", // Description in picker
});


class SensorDataCard extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: "open" });
        this.selectedSensor = "";
        this.selectedArea = "";
        this.sensors = [];
        this.updateInterval = 5;
        this.deadTimeout = 600;
        this.timeoutsPerSensor = {};
        this._intervalId = null;
        this.hideUnavailable = true;

        this.startAutoRefresh();
    }

    startAutoRefresh() {
        if (this._intervalId) {
            clearInterval(this._intervalId);
        }
        this._intervalId = setInterval(() => {
            if (this._hass) {
                this.fetchSensorList();
            }
        }, this.updateInterval * 1000);
    }

    set hass(hass) {
        this._hass = hass;
        if (!this.sensors.length && hass) {
            this.fetchSensorList();
        }
    }

    setConfig(config) {
        this.config = config;
    }

    async fetchSensorList() {
        const listEntity = this._hass.states["sensor.kronoterm_sensor_list"];
        if (listEntity?.attributes?.sensors?.length > 0) {
            this.sensors = listEntity.attributes.sensors;

            const filtered = this.selectedArea
                ? this.sensors.filter(s => s.area === this.selectedArea)
                : this.sensors;

            if (!this.selectedSensor && filtered.length > 0) {
                this.selectedSensor = filtered[0].id;
            }
            const availableAreas = [...new Set(this.sensors.map(s => s.area).filter(Boolean))];
            if (!availableAreas.includes(this.selectedArea)) {
                this.selectedArea = "";
            }


            if (
                !this.shadowRoot.getElementById("sensor-select") ||
                !this.shadowRoot.getElementById("area-select")
            ) {
                this.render();
            } else {
                this.renderAreaDropdown();
                this.renderDropdown();
            }

        }
    }

    handleChange(e) {
        this.selectedSensor = e.target.value;
        this.renderGraph();
    }

    handleRefresh() {
        this._hass.callService("kronoterm_integration", "refresh_sensors");
        setTimeout(() => this.fetchSensorList(), 1000);
    }

    async exportCSV() {
        if (!this.selectedSensor || !this._hass?.auth?.accessToken) {
            alert("Export failed: No sensor selected or missing auth.");
            return;
        }

        const hours = this.config?.hours || 6;
        const url = `/api/kronoterm_integration/history?sensor=${encodeURIComponent(this.selectedSensor)}&hours=${hours}&format=csv`;

        try {
            const response = await fetch(url, {
                method: "GET",
                headers: {
                    "Authorization": `Bearer ${this._hass.auth.accessToken}`,
                    "Accept": "text/csv",
                },
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const blob = await response.blob();
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = `${this.selectedSensor.replace(/\./g, "_")}_history.csv`;
            a.click();
            URL.revokeObjectURL(a.href);
        } catch (err) {
            console.error("CSV export failed:", err);
            alert("CSV export failed. Make sure you're logged in and have access.");
        }
    }

    renderAreaDropdown() {
        const select = this.shadowRoot.getElementById("area-select");
        if (!select) return;

        const areas = [...new Set(this.sensors.map(s => s.area).filter(Boolean))].sort();

        select.innerHTML = `
            <mwc-list-item value="" ${this.selectedArea === "" ? "selected" : ""}></mwc-list-item>
            ${areas.map(area => `
                <mwc-list-item value="${area}" ${this.selectedArea === area ? "selected" : ""}>${area}</mwc-list-item>
            `).join("")}
            `;

        select.value = this.selectedArea;
    }

    isSensorAvailable(sensor) {
        const lastUpdate = sensor.last_updated ? new Date(sensor.last_updated) : null;
        const timeDiff = lastUpdate ? new Date() - lastUpdate : Infinity;
        const timeout = this.timeoutsPerSensor[sensor.id] ?? this.deadTimeout;
        const isAvailable = sensor.available && timeDiff < timeout * 1000;

        return { isAvailable, lastUpdate };
    }

    renderDropdown() {
        const select = this.shadowRoot.getElementById("sensor-select");
        if (!select) return;

        const visibleSensors = (this.selectedArea
            ? this.sensors.filter(s => s.area === this.selectedArea)
            : this.sensors
        ).filter(s => s.id !== "sensor.kronoterm_sensor_list");


        if (!visibleSensors.find(s => s.id === this.selectedSensor)) {
            this.selectedSensor = visibleSensors[0]?.id || "";
        }

        const processedSensors = visibleSensors
            .map(sensor => {
                const { isAvailable, lastUpdate } = this.isSensorAvailable(sensor);
                return { ...sensor, isAvailable, lastUpdate };
            })
            .filter(sensor => !this.hideUnavailable || sensor.isAvailable);

        // Reset selected sensor if no longer visible
        if (!processedSensors.find(s => s.id === this.selectedSensor)) {
            this.selectedSensor = processedSensors[0]?.id || "";
        }

        // Render dropdown
        select.innerHTML = processedSensors.map(sensor => `
        <mwc-list-item
          value="${sensor.id}"
          ${sensor.id === this.selectedSensor ? "selected" : ""}
          style="color: ${sensor.isAvailable ? "white" : "red"};"
        >
          ${sensor.id} ${sensor.isAvailable ? "" : "(Unavailable)"} - ${sensor.lastUpdate ? sensor.lastUpdate.toLocaleTimeString() : ""}
        </mwc-list-item>
    `).join("");
    }

    renderGraph() {
        const graphContainer = this.shadowRoot.getElementById("graph-container");
        if (!graphContainer || !this.selectedSensor) return;

        window.loadCardHelpers().then((helpers) => {
            const cardConfig = {
                type: "custom:plotly-graph",
                entities: [this.selectedSensor],
                hours_to_show: this.config?.hours || 6,
                title: this.selectedSensor,
            };

            const card = helpers.createCardElement(cardConfig);
            card.hass = this._hass;

            graphContainer.innerHTML = "";
            graphContainer.appendChild(card);
        });
    }

    openSettings() {
        const dialog = this.shadowRoot.getElementById("settings-dialog");
        const intervalInput = this.shadowRoot.getElementById("update-interval-input");
        const sensorDropdown = this.shadowRoot.getElementById("sensor-select-settings");
        const timeoutInput = this.shadowRoot.getElementById("dead-timeout-input");
        const unavailableSwitch = this.shadowRoot.getElementById("hide-unavailable-switch");
        if (unavailableSwitch) {
            unavailableSwitch.checked = this.hideUnavailable;
        }

        if (!dialog) return;

        intervalInput.value = this.updateInterval;
        timeoutInput.value = this.deadTimeout;
        sensorDropdown.value = "";

        dialog.showModal();

        sensorDropdown.addEventListener("selected", () => {
            const selectedSensorId = sensorDropdown.value;
            if (selectedSensorId && this.timeoutsPerSensor[selectedSensorId] !== undefined) {
                timeoutInput.value = this.timeoutsPerSensor[selectedSensorId];
            } else {
                timeoutInput.value = this.deadTimeout;
            }
        });

        this.shadowRoot.getElementById("save-settings-btn").onclick = () => {
            const newInterval = parseInt(intervalInput.value, 10);
            const selectedSensor = sensorDropdown.value;
            const newTimeout = parseInt(timeoutInput.value, 10);

            if (!isNaN(newInterval) && newInterval > 0) {
                this.updateInterval = newInterval;
                this.startAutoRefresh();
            }

            if (selectedSensor && !isNaN(newTimeout) && newTimeout > 0) {
                this.timeoutsPerSensor[selectedSensor] = newTimeout;
            } else if (!selectedSensor && !isNaN(newTimeout) && newTimeout > 0) {
                this.deadTimeout = newTimeout;
            }

            if (unavailableSwitch) {
                this.hideUnavailable = unavailableSwitch.checked;
            }

            dialog.close();
            this.fetchSensorList();
        };

        this.shadowRoot.getElementById("close-settings-btn").onclick = () => {
            dialog.close();
        };
    }

    render() {
        if (!this.shadowRoot) return;

        const areas = [...new Set(this.sensors.map(s => s.area).filter(Boolean))];
        console.log("areas", areas)

        this.shadowRoot.innerHTML = `
        <ha-card>
            <div class="card-header-flex">
                <span class="card-title">Sensors Overview</span>
                <mwc-icon-button id="settings-btn" title="Settings">
                <ha-icon icon="mdi:cog"></ha-icon>
                </mwc-icon-button>
            </div>
            <div class="container">
                <style>
                    .card-header-flex {
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        padding: 12px 16px 0 16px;
                        font-size: 1.2em;
                        font-weight: bold;
                    }
                    .card-title {
                    flex: 1 1 auto;
                    }
                    mwc-icon-button[icon="mdi:cog"], mwc-icon-button#settings-btn {
                    --mdc-icon-size: 24px;
                    color: var(--secondary-text-color, #888);
                    }
                    select, button {
                    margin-bottom: 10px;
                    font-size: 14px;
                    padding: 6px;
                    }
                    .container {
                    padding: 16px;
                    }
                    dialog::backdrop {
                    background-color: rgba(0, 0, 0, 0.5);
                    }
                    #graph-container {
                    margin: 20px 0 10px 0;
                    }
                    dialog {
                    border: none;
                    border-radius: 8px;
                    padding: 0;
                    overflow: visible;
                    }
                    ha-select, ha-textfield {
                    width: 100%;
                    margin-top: 10px;
                    margin-bottom: 10px;
                    }
                    .subsection-header {
                        font-size: 1rem;
                        font-weight: 600;
                        color: var(--secondary-text-color, #666);
                        margin-bottom: 0px;
                        margin-top: 2px;
                        letter-spacing: 0.03em;
                        }
                </style>
                <div>
                    <div class="subsection-header">Area</div>
                    <ha-select id="area-select" label="Area"></ha-select>

                    <div class="subsection-header">Sensor</div>
                    <ha-select id="sensor-select" label="Sensor"></ha-select>

                    <div id="graph-container"></div>

                    <mwc-button id="refresh-btn" outlined><ha-icon icon="mdi:reload" style="--mdc-icon-size: 20px; margin-right: 10px;"></ha-icon>Refresh</mwc-button>
                    <mwc-button id="export-csv-btn" outlined>
                        <ha-icon icon="mdi:download" style="--mdc-icon-size: 20px; margin-right: 10px;"></ha-icon>
                        Export CSV
                    </mwc-button>
                </div>
                <dialog id="settings-dialog">
                    <ha-card header="Sensor Settings">
                    <div class="card-content">
                        <div style="display: flex; align-items: center; margin-bottom: 30px;">
                            <ha-switch id="hide-unavailable-toggle"></ha-switch>
                            <span style="margin-left: 8px;">Hide Unavailable Sensors</span>
                        </div>

                        <label for="update-interval-input">Global sensor value refresh:</label>
                        <ha-textfield
                        label="Update Interval (seconds)"
                        id="update-interval-input"
                        type="number"
                        min="1"
                        style="margin-bottom: 30px;"
                        ></ha-textfield>

                        <label for="sensor-select-settings">Select sensor to set timeout:</label>
                        <ha-select label="Sensor" id="sensor-select-settings">
                        <mwc-list-item value=""></mwc-list-item>
                        ${this.sensors.map(sensor => `
                            <mwc-list-item value="${sensor.id}">${sensor.id}</mwc-list-item>
                        `).join("")}
                        </ha-select>

                        <label for="dead-timeout-input">Dead timeout for selected sensor (global if not selected):</label>
                        <ha-textfield
                        label="Dead Timeout (seconds)"
                        id="dead-timeout-input"
                        type="number"
                        min="1"
                        ></ha-textfield>

                        <mwc-button id="save-settings-btn" raised>Save</mwc-button>
                        <mwc-button id="close-settings-btn" outlined>Close</mwc-button>
                    </div>
                    </ha-card>
                </dialog>
            </ha-card>
            `;

        this.shadowRoot.getElementById("sensor-select")?.addEventListener("change", (e) => this.handleChange(e));
        this.shadowRoot.getElementById("area-select")?.addEventListener("change", (e) => {
            this.selectedArea = e.target.value;
            this.selectedSensor = "";
            this.renderDropdown();
            this.renderGraph();
        });
        this.shadowRoot.getElementById("refresh-btn")?.addEventListener("click", () => this.handleRefresh());
        this.shadowRoot.getElementById("settings-btn")?.addEventListener("click", () => this.openSettings());
        this.shadowRoot.getElementById("export-csv-btn")?.addEventListener("click", () => this.exportCSV());

        this.renderDropdown();
        this.renderGraph();

        const toggle = this.shadowRoot.getElementById("hide-unavailable-toggle");
        if (toggle) {
            toggle.checked = this.hideUnavailable;
            toggle.addEventListener("change", (e) => {
                this.hideUnavailable = e.target.checked;
            });
        }
    }

    getCardSize() {
        return 3;
    }
}

customElements.define("sensor-data-card", SensorDataCard);
