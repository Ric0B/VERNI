// Thin wrapper around Leaflet (loaded as a classic script, global L). One map per container.

const TILES = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
const ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors';

export function createMap(el, { wheel = false, touchDrag = true } = {}) {
  const L = window.L;
  if (!L) { el.innerHTML = '<p class="map-missing">The map could not be loaded.</p>'; return null; }
  const map = L.map(el, {
    scrollWheelZoom: wheel,
    dragging: touchDrag || !L.Browser.mobile,
    tap: false,
    worldCopyJump: false,
    zoomAnimation: false,   // an animation timer firing after the map is removed throws inside Leaflet
    markerZoomAnimation: false,
  }).setView([46.8, 8.2], 7);
  L.tileLayer(TILES, { maxZoom: 19, attribution: ATTRIBUTION }).addTo(map);

  const layer = L.layerGroup().addTo(map);
  const markers = new Map();
  let line = null;
  let onClick = () => {};
  let selectedId = null;

  const iconFor = (pin, selected) => L.divIcon({
    className: "pin-wrap",
    html: `<span class="pin${selected ? " sel" : ""}${pin.small ? " sm" : ""}">${pin.label ?? ""}</span>`,
    iconSize: selected ? [38, 38] : [30, 30],
    iconAnchor: selected ? [19, 19] : [15, 15],
  });

  return {
    setPins(pins, { click, fit = true } = {}) {
      onClick = click || onClick;
      layer.clearLayers();
      markers.clear();
      selectedId = null;
      for (const pin of pins) {
        const m = L.marker([pin.lat, pin.lon], { icon: iconFor(pin, !!pin.selected), title: pin.title || "", keyboard: true, riseOnHover: true });
        m.on("click", () => onClick(pin.id));
        if (pin.popup) m.bindPopup(pin.popup, { closeButton: false, offset: [0, -8] });
        m.addTo(layer);
        markers.set(pin.id, { m, pin });
        if (pin.selected) selectedId = pin.id;
      }
      if (fit) this.fit(pins);
    },
    select(id, { pan = true } = {}) {
      if (id === selectedId) return;
      for (const pid of [selectedId, id]) {
        const entry = pid && markers.get(pid);
        if (!entry) continue;
        entry.m.setIcon(iconFor(entry.pin, pid === id));
        entry.m.setZIndexOffset(pid === id ? 1000 : 0);
      }
      selectedId = id;
      const hit = pan && markers.get(id);
      if (hit && !map.getBounds().pad(-0.1).contains(hit.m.getLatLng())) map.panTo(hit.m.getLatLng(), { animate: false });
    },
    openPopup(id) { const hit = markers.get(id); if (hit) hit.m.openPopup(); },
    setRoute(coords) {
      if (line) { line.remove(); line = null; }
      if (coords.length > 1) {
        line = L.polyline(coords, { color: getComputedStyle(document.documentElement).getPropertyValue("--mark").trim() || "#5b3cff", weight: 4, opacity: 0.9 }).addTo(map);
      }
    },
    fit(pins) {
      const pts = pins.map((p) => [p.lat, p.lon]);
      if (!pts.length) { map.setView([46.8, 8.2], 7, { animate: false }); return; }
      if (pts.length === 1) { map.setView(pts[0], 15, { animate: false }); return; }
      map.fitBounds(L.latLngBounds(pts), { padding: [36, 36], maxZoom: 15, animate: false });
    },
    invalidate() { map.invalidateSize(); },
    destroy() { map.stop(); map.off(); map.remove(); },
  };
}
