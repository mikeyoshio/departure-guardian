class DepartureGuardianMapCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity) {
      throw new Error("Debes indicar 'entity' (el binary_sensor de Departure Guardian)");
    }
    this._config = config;
    this._editMode = false;

    if (!this._built) {
      this._built = true;
      this.innerHTML = `
        <ha-card>
          <div class="dg-toolbar">
            <select class="dg-entity-select"></select>
            <button class="dg-edit-btn" type="button">Editar posiciones</button>
          </div>
          <div class="dg-map-wrap">
            <img class="dg-map-img" alt="Plano" />
            <div class="dg-markers"></div>
          </div>
          <style>
            ha-card { overflow: hidden; }
            .dg-toolbar { display:flex; gap:8px; padding:8px 16px; align-items:center; }
            .dg-entity-select { flex: 1; }
            .dg-map-wrap { position: relative; width: 100%; background: var(--card-background-color); }
            .dg-map-img { width: 100%; display:block; }
            .dg-markers { position:absolute; inset:0; pointer-events:none; }
            .dg-marker {
              position:absolute; width:16px; height:16px; border-radius:50%;
              transform:translate(-50%,-50%); border:2px solid white;
              box-shadow:0 0 4px rgba(0,0,0,.6);
            }
            .dg-marker.ok { background:#2e7d32; }
            .dg-marker.problem { background:#c62828; }
            .dg-edit-btn.active { outline:2px solid var(--primary-color); }
            .dg-hint { padding: 0 16px 8px; font-size: 12px; color: var(--secondary-text-color); }
          </style>
        </ha-card>
      `;
      this._img = this.querySelector(".dg-map-img");
      this._markersEl = this.querySelector(".dg-markers");
      this._select = this.querySelector(".dg-entity-select");
      this._editBtn = this.querySelector(".dg-edit-btn");

      this._editBtn.addEventListener("click", () => {
        this._editMode = !this._editMode;
        this._editBtn.classList.toggle("active", this._editMode);
      });
      this._img.addEventListener("click", (ev) => this._handleMapClick(ev));
    }

    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _handleMapClick(ev) {
    if (!this._editMode || !this._hass) return;
    const entityId = this._select.value;
    if (!entityId || !this._configEntryId) return;

    const rect = this._img.getBoundingClientRect();
    const x = Math.round((((ev.clientX - rect.left) / rect.width) * 100) * 10) / 10;
    const y = Math.round((((ev.clientY - rect.top) / rect.height) * 100) * 10) / 10;

    this._hass.callService("departure_guardian", "set_position", {
      config_entry_id: this._configEntryId,
      entity_id: entityId,
      x,
      y,
    });
  }

  _render() {
    if (!this._hass || !this._config || !this._img) return;
    const state = this._hass.states[this._config.entity];
    if (!state) return;

    const attrs = state.attributes;
    this._configEntryId = attrs.config_entry_id;

    let imgUrl = attrs.map_image;
    if (!imgUrl && attrs.map_camera && this._hass.states[attrs.map_camera]) {
      imgUrl = this._hass.states[attrs.map_camera].attributes.entity_picture;
    }
    if (imgUrl) {
      const fullUrl = imgUrl.startsWith("http") ? imgUrl : this._hass.hassUrl(imgUrl);
      if (this._img.src !== fullUrl) this._img.src = fullUrl;
    }

    const statuses = attrs.statuses || [];
    const positions = attrs.positions || {};
    const previousValue = this._select.value;

    this._select.innerHTML = statuses
      .map((s) => `<option value="${s.entity_id}">${s.label}</option>`)
      .join("");
    if (previousValue) this._select.value = previousValue;

    this._markersEl.innerHTML = "";
    for (const status of statuses) {
      const pos = positions[status.entity_id];
      if (!pos) continue;
      const marker = document.createElement("div");
      marker.className = `dg-marker ${status.problem ? "problem" : "ok"}`;
      marker.style.left = `${pos.x}%`;
      marker.style.top = `${pos.y}%`;
      marker.title = status.detail || status.label;
      this._markersEl.appendChild(marker);
    }
  }

  getCardSize() {
    return 4;
  }
}

customElements.define("departure-guardian-map-card", DepartureGuardianMapCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "departure-guardian-map-card",
  name: "Departure Guardian Map",
  description:
    "Plano de la vivienda con el estado en vivo de las entidades vigiladas por Departure Guardian.",
});
