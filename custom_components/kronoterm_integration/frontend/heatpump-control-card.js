window.customCards = window.customCards || [];
window.customCards.push({
  type: "heatpump-control-card",        // Your card's type
  name: "Heatpump control card",        // Display name in card picker
  preview: true,                   // Optional: enable preview image
  description: "Shows Kronoterm heatpump sensors and provides control for the heatpump.", // Description in picker
});

class HeatpumpControlCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.desiredTemp = 20;
    this.entityId = "sensor.kronoterm_desired_temperature";
    this.sensors = [];
    this.binarySensors = [];
    this.enumSensors = [];
    this.updateInterval = 60;
    this._intervalId = null;
    this.additionalSourceEnabled = false;
    this.dhwCirculationEnabled = false;
  }

  connectedCallback() {
    this.renderLayout();
    this.startAutoRefresh();
    this.fetchSensorList();
  }

  set hass(hass) {
    this._hass = hass;
    this.additionalSourceEnabled = hass.states["switch.additional_source_callback"]?.state === "on";
    this.dhwCirculationEnabled = hass.states["switch.dhw_circulation_switch"]?.state === "on";
    this.desiredTemp = parseFloat(hass.states["number.loop_1_target_temperature"]?.state || "20");
  }

  setConfig(config) {
    this.config = config;
    window.heatpumpCard = this;
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

  async fetchSensorList() {
    const listEntity = this._hass?.states?.["sensor.kronoterm_sensor_list"];
    if (listEntity?.attributes?.sensors?.length > 0) {
      const sensorList = listEntity.attributes.sensors;
      this.sensors = sensorList.filter(obj => obj.id.startsWith("sensor.") && obj.kronoterm);
      this.binarySensors = sensorList.filter(obj => obj.id.startsWith("binary_sensor.") && obj.kronoterm);
      this.enumSensors = sensorList.filter(obj => obj.id.startsWith("enum.") && obj.kronoterm);
      this.updateSensorValues();
    }
  }

  updateSensorValues() {
    const container = this.shadowRoot.getElementById("sensor-container");
    if (!container) return;

    container.innerHTML = `
      ${this.renderSensors(this.sensors)}
      ${this.renderBinarySensors(this.binarySensors)}
      ${this.renderEnumSensors(this.enumSensors)}
    `;
  }

  renderSensors(entities) {
    return entities.map(entity => {
      const icon = this.getIcon(entity.id);
      const value = entity.unit ? `${entity.state} ${entity.unit}` : entity.state;
      return `
        <div class="sensor-row">
          <div class="sensor-label">
            <ha-icon icon="${icon}"></ha-icon>
            <span>${entity.name}</span>
          </div>
          <div>${value}</div>
        </div>
      `;
    }).join("");
  }

  renderBinarySensors(entities) {
    return entities.map(entity => {
      const icon = this.getIcon(entity.id);
      const value = entity.state === "on" ? "On" : "Off";
      return `
        <div class="sensor-row">
          <div class="sensor-label">
            <ha-icon icon="${icon}"></ha-icon>
            <span>${entity.name}</span>
          </div>
          <div>${value}</div>
        </div>
      `;
    }).join("");
  }

  renderEnumSensors(entities) {
    return entities.map(entity => {
      const icon = this.getIcon(entity.id);
      return `
        <div class="sensor-row">
          <div class="sensor-label">
            <ha-icon icon="${icon}"></ha-icon>
            <span>${entity.name}</span>
          </div>
          <div>${entity.state}</div>
        </div>
      `;
    }).join("");
  }

  getIcon(entityId) {
    if (entityId.includes("temperature")) return "mdi:thermometer";
    if (entityId.includes("power")) return "mdi:flash";
    if (entityId.includes("pressure")) return "mdi:gauge";
    if (entityId.includes("pump")) return "mdi:pump";
    if (entityId.includes("source")) return "mdi:lightning-bolt-circle";
    if (entityId.includes("load")) return "mdi:gauge";
    return "mdi:information-outline";
  }

  openSettings() {
    const dialog = this.shadowRoot.getElementById("settings-dialog");
    const slider = this.shadowRoot.getElementById("loop1-slider");

    if (!dialog) return;

    slider.value = this.desiredTemp;
    dialog.showModal();


    const valueLabel = this.shadowRoot.getElementById("slider-value-label");
    valueLabel.textContent = slider.value;

    slider.addEventListener("input", () => {
      valueLabel.textContent = slider.value;
    });

    const additionalToggle = this.shadowRoot.getElementById("additional-source-toggle");
    const dhwToggle = this.shadowRoot.getElementById("dhw-circulation-toggle");

    additionalToggle.checked = this.additionalSourceEnabled;
    dhwToggle.checked = this.dhwCirculationEnabled;

    additionalToggle.addEventListener("change", () => {
      this.additionalSourceEnabled = additionalToggle.checked;
    });

    dhwToggle.addEventListener("change", () => {
      this.dhwCirculationEnabled = dhwToggle.checked;
    });

    this.shadowRoot.getElementById("save-settings-btn").onclick = () => {
      const newDesiredTemp = parseFloat(slider.value, 10);

      if (!isNaN(newDesiredTemp) && newDesiredTemp >= 0 && newDesiredTemp <= 100) {
        this.desiredTemp = newDesiredTemp;

        this._hass.callService("number", "set_value", {
          entity_id: "number.loop_1_target_temperature",
          value: newDesiredTemp,
        });
      } else {
        alert("Please enter a valid temperature between 10 and 30 degrees.");
      }

      this._hass.callService("switch", this.dhwCirculationEnabled ? "turn_on" : "turn_off", {
        entity_id: "switch.dhw_circulation_switch"
      });

      this._hass.callService("switch", this.additionalSourceEnabled ? "turn_on" : "turn_off", {
        entity_id: "switch.additional_source_callback"
      });
      this.renderLayout()
      dialog.close();
    };

    this.shadowRoot.getElementById("close-settings-btn").onclick = () => {
      dialog.close();
    };
  }

  renderLayout() {
    this.shadowRoot.innerHTML = `
      <style>
        ha-card {
          padding: 16px;
        }
        .sensor-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 4px 0;
          color: var(--primary-text-color);
        }
        ha-icon {
          margin-right: 8px;
          color: var(--secondary-text-color);
        }
        .sensor-label {
          display: flex;
          align-items: center;
        }
        .container {
          padding: 16px;
        }
        dialog::backdrop {
          background-color: rgba(0, 0, 0, 0.5);
        }
        dialog {
          border: none;
          border-radius: 8px;
          padding: 0;
          overflow: visible;
        }
        ha-slider {
          width: 100%;
        }
        #desired-temp-input {
          width: 100%;
          margin-top: 10px;
        }
        .slider-row {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-top: 10px;
        }
        .slider-value {
          font-size: 16px;
          width: 40px;
          text-align: right;
        }
      </style>

      <ha-card header="Heat Pump Control">
        <div class="container">
          <div id="sensor-container"></div>
          <mwc-button id="settings-btn" raised>
            <ha-icon icon="mdi:cog" style="--mdc-icon-size: 20px; margin-right: 10px;"></ha-icon>Set parameters
          </mwc-button>
        </div>
      </ha-card>

      <dialog id="settings-dialog">
        <ha-card header="Sensor Settings">
          <div class="card-content">
            <div class="sensor-row">
              <div class="sensor-label">
                <ha-icon icon="mdi:thermometer"></ha-icon>
                <span>Loop 1 Target Temperature</span>
              </div>
              <div class="slider-row">
                <ha-slider
                  min="5"
                  max="80"
                  step="0.5"
                  id="loop1-slider"
                ></ha-slider>
                <span id="slider-value-label" class="slider-value">--</span>
              </div>
            </div>
            <div class="sensor-row">
              <div class="sensor-label">
                <ha-icon icon="mdi:flash"></ha-icon>
                <span>Additional Source Callback</span>
              </div>
              <ha-switch id="additional-source-toggle" ?checked=${this.additionalSourceEnabled}></ha-switch>
            </div>

            <div class="sensor-row">
              <div class="sensor-label">
                <ha-icon icon="mdi:water-pump"></ha-icon>
                <span>DHW Circulation</span>
              </div>
              <ha-switch id="dhw-circulation-toggle" ?checked=${this.dhwCirculationEnabled}></ha-switch>
            </div>
            <div style="margin-top: 16px;">
              <mwc-button id="save-settings-btn" raised>Save</mwc-button>
              <mwc-button id="close-settings-btn" outlined>Close</mwc-button>
            </div>
          </div>
        </ha-card>
      </dialog>
    `;

    this.shadowRoot.getElementById("settings-btn")
      .addEventListener("click", () => this.openSettings());
  }

  getCardSize() {
    return 3;
  }
}

customElements.define("heatpump-control-card", HeatpumpControlCard);
