window.customCards = window.customCards || [];
window.customCards.push({
  type: "heatpump-control-card",
  name: "Heatpump control card",
  preview: true,
  description: "Shows Kronoterm heatpump sensors and provides control for the heatpump.",
});

// Hardcoded control definitions
const CONTROL_SWITCHES = [
  { id: "switch.additional_source_switch", name: "Additional source" },
  { id: "switch.error_reset", name: "Error reset" },
  { id: "switch.loop_1_adaptive_curve", name: "Loop 1 adaptive curve" },
  { id: "switch.loop_2_adaptive_curve", name: "Loop 2 adaptive curve" },
  { id: "switch.home_water_switch", name: "Home water switch" },
];

const CONTROL_NUMBERS = [
  {
    id: "number.loop_1_heat_curve_lower_point",
    name: "Loop 1 heat curve lower point",
    min: 25.0,
    max: 50.0,
    step: 0.5,
    unit: "°C",
  },
  {
    id: "number.loop_1_heat_curve_upper_point",
    name: "Loop 1 heat curve upper point",
    min: 25.0,
    max: 50.0,
    step: 0.5,
    unit: "°C",
  },
  {
    id: "number.loop_2_heat_curve_lower_point",
    name: "Loop 2 heat curve lower point",
    min: 25.0,
    max: 50.0,
    step: 0.5,
    unit: "°C",
  },
  {
    id: "number.loop_2_heat_curve_upper_point",
    name: "Loop 2 heat curve upper point",
    min: 25.0,
    max: 50.0,
    step: 0.5,
    unit: "°C",
  },
  {
    id: "number.set_desired_hw_temperature",
    name: "Set Desired HW temperature",
    min: 25.0,
    max: 50.0,
    step: 0.5,
    unit: "°C",
  },
];

class HeatpumpControlCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });

    this.sensors = [];
    this.binarySensors = [];
    this.enumSensors = [];
    this.errorSensors = [];
    this.regularSensors = [];
    this.updateInterval = 5;
    this._intervalId = null;
    this._userEditing = false;
    this._controls = {}; // user-chosen values

    this._errorsExpanded = false;
    this._sensorsExpanded = true;
  }

  connectedCallback() {
    this.renderLayout();
    this.startAutoRefresh();
    this.fetchSensorList();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._userEditing) this.syncControlsFromHass();
  }

  setConfig(config) {
    this.config = config;
    window.heatpumpCard = this;
  }

  startAutoRefresh() {
    if (this._intervalId) clearInterval(this._intervalId);
    this._intervalId = setInterval(() => {
      if (this._hass) this.fetchSensorList();
    }, this.updateInterval * 1000);
  }

  async fetchSensorList() {
    const listEntity = this._hass?.states?.["sensor.kronoterm_sensor_list"];
    if (listEntity?.attributes?.sensors?.length > 0) {
      const sensorList = listEntity.attributes.sensors;
      this.sensors = sensorList.filter(obj => obj.id.startsWith("sensor.") && obj.kronoterm && obj.type !== "enum");
      this.binarySensors = sensorList.filter(obj => obj.id.startsWith("binary_sensor.") && obj.kronoterm);
      this.enumSensors = sensorList.filter(obj => obj.id.startsWith("sensor.") && obj.type === "enum" && obj.kronoterm);

      // Group error sensors and regular sensors
      this.errorSensors = this.sensors.filter(obj =>
        (obj.name && obj.name.toLowerCase().includes("error")) ||
        (obj.id && obj.id.toLowerCase().includes("error"))
      );
      this.regularSensors = this.sensors.filter(obj =>
        !((obj.name && obj.name.toLowerCase().includes("error")) ||
          (obj.id && obj.id.toLowerCase().includes("error")))
      );

      this.updateSensorValues();
    }
  }

  syncControlsFromHass() {
    if (!this._hass) return;
    // Sync switches
    for (const sw of CONTROL_SWITCHES) {
      const entity = this._hass.states?.[sw.id];
      this._controls[sw.id] = entity?.state === "on";
    }
    // Sync numbers
    for (const num of CONTROL_NUMBERS) {
      const entity = this._hass.states?.[num.id];
      let val = entity ? parseFloat(entity.state) : num.min;
      if (isNaN(val)) val = num.min;
      this._controls[num.id] = val;
    }
    this.renderParameterControls();
  }

  // --- PARAMETERS CONTROLS UI ---
  renderParameterControls() {
    const container = this.shadowRoot.getElementById("parameter-controls");
    if (!container) return;
    container.innerHTML = `
      ${CONTROL_SWITCHES.map(sw => `
        <div class="parameter-row">
          <span class="parameter-label"><ha-icon icon="mdi:toggle-switch"></ha-icon>${sw.name}</span>
          <ha-switch id="switch-${sw.id}"></ha-switch>
        </div>
      `).join("")}
      ${CONTROL_NUMBERS.map(num => `
        <div class="parameter-row">
          <span class="parameter-label"><ha-icon icon="mdi:thermometer"></ha-icon>${num.name}</span>
          <div class="slider-row" style="flex:1;">
            <ha-slider id="slider-${num.id}" min="${num.min}" max="${num.max}" step="${num.step}" style="flex:1;"></ha-slider>
            <span id="slider-value-${num.id}" class="slider-value"></span>
            <span class="slider-unit">${num.unit}</span>
          </div>
        </div>
      `).join("")}
    `;

    // Set current values and event listeners
    for (const sw of CONTROL_SWITCHES) {
      const el = this.shadowRoot.getElementById(`switch-${sw.id}`);
      if (el) {
        el.checked = !!this._controls[sw.id];
        el.addEventListener("change", () => {
          this._controls[sw.id] = el.checked;
          this._userEditing = true;
        });
      }
    }
    for (const num of CONTROL_NUMBERS) {
      const slider = this.shadowRoot.getElementById(`slider-${num.id}`);
      const valueLabel = this.shadowRoot.getElementById(`slider-value-${num.id}`);
      if (slider && valueLabel) {
        slider.value = this._controls[num.id];
        valueLabel.textContent = this._controls[num.id];
        slider.addEventListener("input", () => {
          valueLabel.textContent = slider.value;
          this._controls[num.id] = parseFloat(slider.value);
          this._userEditing = true;
        });
      }
    }
    const saveBtn = this.shadowRoot.getElementById("save-settings-btn");
    if (saveBtn) {
      saveBtn.onclick = () => {
        // Save switches
        for (const sw of CONTROL_SWITCHES) {
          const checked = this.shadowRoot.getElementById(`switch-${sw.id}`).checked;
          this._hass.callService("switch", checked ? "turn_on" : "turn_off", { entity_id: sw.id });
        }
        // Save numbers
        for (const num of CONTROL_NUMBERS) {
          const val = parseFloat(this.shadowRoot.getElementById(`slider-${num.id}`).value);
          this._hass.callService("number", "set_value", { entity_id: num.id, value: val });
        }
        this._userEditing = false;
      };
    }
  }

  // --- SENSORS DISPLAY ---
  updateSensorValues() {
    const container = this.shadowRoot.getElementById("sensor-container");
    if (!container) return;
    // Error coloring for error section header
    let errorHeaderColor = "inherit";
    let hasRed = false;
    let hasOrange = false;
    for (const sensor of this.errorSensors) {
      const state = typeof sensor.state === "string" ? sensor.state.toLowerCase() : "";
      if (state !== "no error" && state !== "unknown" && state.trim() !== "") {
        hasRed = true; break;
      }
      if (state === "unknown") hasOrange = true;
    }
    if (hasRed) errorHeaderColor = "var(--error-color, #c00)";
    else if (hasOrange) errorHeaderColor = "orange";

    const otherSensorsHTML = [
      ...this.renderSensors(this.regularSensors),
      ...this.renderBinarySensors(this.binarySensors),
      ...this.renderEnumSensors(this.enumSensors)
    ].join("");

    container.innerHTML = `
      ${this.renderErrorExpandableSection(
      "Error Registers",
      "alert-circle-outline",
      this.renderErrorSensors(this.errorSensors).join(""),
      this._errorsExpanded,
      "errors",
      errorHeaderColor
    )}
      ${this.renderExpandableSection(
      "Sensors",
      "gauge",
      otherSensorsHTML,
      this._sensorsExpanded,
      "sensors"
    )}
    `;

    // Expand/collapse listeners
    ["errors", "sensors"].forEach(key => {
      const header = this.shadowRoot.getElementById(`expander-header-${key}`);
      if (header) {
        header.onclick = () => {
          if (key === "errors") this._errorsExpanded = !this._errorsExpanded;
          else if (key === "sensors") this._sensorsExpanded = !this._sensorsExpanded;
          this.updateSensorValues();
        };
      }
    });
  }

  renderErrorExpandableSection(label, icon, content, expanded, key, headerColor) {
    return `
      <div class="expander">
        <div class="expander-header" id="expander-header-${key}" style="color: ${headerColor};">
          <ha-icon icon="mdi:${icon}"></ha-icon>
          <span>${label}</span>
          <ha-icon icon="mdi:${expanded ? "chevron-up" : "chevron-down"}" class="expander-arrow"></ha-icon>
        </div>
        <div class="expander-content" style="display: ${expanded ? "block" : "none"};">
          ${content || "<div class='empty-section'>No error sensors found</div>"}
        </div>
      </div>
    `;
  }

  renderExpandableSection(label, icon, content, expanded, key) {
    return `
      <div class="expander">
        <div class="expander-header" id="expander-header-${key}">
          <ha-icon icon="mdi:${icon}"></ha-icon>
          <span>${label}</span>
          <ha-icon icon="mdi:${expanded ? "chevron-up" : "chevron-down"}" class="expander-arrow"></ha-icon>
        </div>
        <div class="expander-content" style="display: ${expanded ? "block" : "none"};">
          ${content || "<div class='empty-section'>No data</div>"}
        </div>
      </div>
    `;
  }

  // Only color the error state value text
  renderErrorSensors(entities) {
    if (!entities || !entities.length) return [];
    return entities.map(entity => {
      const icon = this.getIcon(entity.id);
      let value = entity.unit ? `${entity.state} ${entity.unit}` : entity.state;
      let valueColor = "";
      const state = typeof entity.state === "string" ? entity.state.toLowerCase() : "";
      if (state !== "no error" && state !== "unknown" && state.trim() !== "") {
        valueColor = "color: var(--error-color, #c00); font-weight: bold;";
      } else if (state === "unknown") {
        valueColor = "color: orange; font-weight: bold;";
      }
      return `
        <div class="sensor-row">
          <div class="sensor-label">
            <ha-icon icon="${icon}"></ha-icon>
            <span>${entity.name}</span>
          </div>
          <div style="${valueColor}">${value}</div>
        </div>
      `;
    });
  }

  renderSensors(entities) {
    if (!entities || !entities.length) return [];
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
    });
  }

  renderBinarySensors(entities) {
    if (!entities || !entities.length) return [];
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
    });
  }

  renderEnumSensors(entities) {
    if (!entities || !entities.length) return [];
    return entities.map(entity => {
      const icon = this.getIcon(entity.id);
      const isError = /Error/i.test(entity.name) && !/No error/i.test(entity.state);
      return `
        <div class="sensor-row ${isError ? "error" : "noError"}">
          <div class="sensor-label">
            <ha-icon icon="${icon}"></ha-icon>
            <span>${entity.name}</span>
          </div>
          <div>${entity.state}</div>
        </div>
      `;
    });
  }

  getIcon(entityId) {
    if (entityId.includes("temperature")) return "mdi:thermometer";
    if (entityId.includes("power")) return "mdi:flash";
    if (entityId.includes("pressure")) return "mdi:gauge";
    if (entityId.includes("pump")) return "mdi:pump";
    if (entityId.includes("source")) return "mdi:lightning-bolt-circle";
    if (entityId.includes("load")) return "mdi:gauge";
    if (entityId.includes("error")) return "mdi:alert-circle-outline";
    return "mdi:information-outline";
  }

  renderLayout() {
    this.shadowRoot.innerHTML = `
      <style>
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
        .expander {
          border-radius: 8px;
          border: 1px solid var(--divider-color, #e0e0e0);
          margin-bottom: 10px;
          background: var(--card-background-color, #fff);
          box-shadow: var(--ha-card-box-shadow);
          overflow: hidden;
        }
        .expander-header {
          display: flex;
          align-items: center;
          cursor: pointer;
          padding: 8px 12px;
          font-weight: 500;
          background: var(--secondary-background-color, #f6f7f9);
          transition: background 0.2s;
        }
        .expander-header:hover {
          background: var(--primary-background-color, #f0f0f0);
        }
        .expander-header ha-icon {
          margin-right: 8px;
        }
        .expander-arrow {
          margin-left: auto;
          transition: transform 0.2s;
        }
        .expander-content {
          padding: 4px 12px 8px 12px;
        }
        .empty-section {
          color: var(--disabled-text-color, #999);
          font-style: italic;
          padding: 8px 0;
        }
        .card-header-flex {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 25px 16px 10px 16px;
          font-size: 1.2em;
          font-weight: bold;
        }
        .card-title {
          flex: 1 1 auto;
        }
        .parameters-section {
          margin: 0 0 16px 0;
          padding: 16px 12px 8px 12px;
          border-radius: 8px;
          border: 1px solid var(--divider-color, #e0e0e0);
          background: var(--secondary-background-color, #f6f7f9);
        }
        .parameter-row {
          display: flex;
          align-items: center;
          margin-bottom: 12px;
        }
        .parameter-label {
          font-weight: 500;
          margin-right: 15px;
          display: flex;
          align-items: center;
        }
        .slider-row {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .slider-value {
          font-size: 16px;
          width: 48px;
          text-align: right;
        }
        .slider-unit {
          font-size: 16px;
          margin-left: 2px;
          color: var(--primary-text-color);
        }
        mwc-button {
          margin-bottom: 40px;
        }
        .subsection-header {
          font-size: 1rem;
          font-weight: 600;
          color: var(--secondary-text-color, #666);
          margin-bottom: 15px;
          margin-top: 2px;
          letter-spacing: 0.03em;
        }
      </style>
      <ha-card>
        <div class="card-header-flex">
            <span class="card-title">Heat Pump Control</span>
        </div>
        <div class="container">
          <div class="subsection-header">Control Parameters</div>
          <div class="parameters-section" id="parameter-controls"></div>
          <mwc-button id="save-settings-btn" raised>Apply settings</mwc-button>
          <div class="subsection-header">Heatpump Sensors</div>
          <div id="sensor-container"></div>
        </div>
      </ha-card>
    `;
    this.renderParameterControls();
    this.updateSensorValues();
  }

  getCardSize() {
    return 4;
  }
}

customElements.define("heatpump-control-card", HeatpumpControlCard);
