import {
  REGIONS, CITIES, TYPES, TYPE_ORDER, EVENT_TYPES, cityOf, cityLabel,
  TODAY, addDays, diffDays, fDate, fWeekday, fDayLong,
  loadListings, buildModel, status, isVisible, isCurrent, closingSoon, dateRange, isOpenNow, hoursText, walkKm,
} from "./data.js";
import { createMap } from "./map.js";

const $ = (s, r = document) => r.querySelector(s);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const store = {
  get(k, d) { try { const v = localStorage.getItem("verni:" + k); return v == null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem("verni:" + k, JSON.stringify(v)); } catch { /* storage unavailable */ } },
};

/* ---------- icons ---------- */
const svg = (d, s = 22, w = 1.75, fill = "none") => `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="${fill}" stroke="currentColor" stroke-width="${w}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${d}</svg>`;
const HEART = '<path d="M12 20.5s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7.8a4.3 4.3 0 0 1 7.5 2.5C19.5 15.9 12 20.5 12 20.5z"/>';
const PIN = '<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>';
const I = {
  heart: svg(HEART), heartFill: svg(HEART, 22, 1.75, "currentColor"),
  list: svg('<rect x="4" y="4" width="16" height="7" rx="2"/><rect x="4" y="13" width="16" height="7" rx="2"/>'),
  cal: svg('<rect x="4" y="5.5" width="16" height="14.5" rx="2.5"/><path d="M4 10h16M8.5 3.5v4M15.5 3.5v4"/>'),
  pin: svg(PIN), pinS: svg(PIN, 18, 2),
  route: svg('<circle cx="6" cy="18" r="2.3"/><circle cx="18" cy="6" r="2.3"/><path d="M8.3 18H15a3 3 0 0 0 0-6H9a3 3 0 0 1 0-6h6.7"/>'),
  plus: svg('<path d="M12 5v14M5 12h14"/>', 16, 2.2), check: svg('<path d="M5 12.5l4.5 4.5L19 7.5"/>', 16, 2.2),
  chev: svg('<path d="M7 10l5 5 5-5"/>', 16, 2), back: svg('<path d="M14.5 5.5L8 12l6.5 6.5"/>', 16, 2),
  next: svg('<path d="M9.5 5.5L16 12l-6.5 6.5"/>', 18, 1.9), ext: svg('<path d="M7 17L17 7M9 7h8v8"/>', 16, 2.2),
  up: svg('<path d="M6 14l6-6 6 6"/>', 20, 2), down: svg('<path d="M6 10l6 6 6-6"/>', 20, 2), x: svg('<path d="M6 6l12 12M18 6L6 18"/>', 20, 2),
  search: svg('<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>', 20),
  bell: svg('<path d="M6 16.5V11a6 6 0 0 1 12 0v5.5l1.5 1.5h-15z"/><path d="M10 20.5a2 2 0 0 0 4 0"/>', 16, 2),
};

/* ---------- state ---------- */
let M = null;                       // the listings model
let loadedFromCache = false;
const state = {
  scope: store.get("scope", "switzerland"), view: "exhibitions", param: null,
  openNow: false, type: "all", q: "", evType: "all", venueType: "all", venueOpen: false, venueQ: "", artistQ: "",
  mapSel: null,
  tour: store.get("tour", []), favs: store.get("favs", []), tourOrder: store.get("tourOrder", "custom") === "shortest" ? "shortest" : "custom",
};
const desktop = window.matchMedia("(min-width: 900px)");

/* ---------- scope ---------- */
function parseScope(tok) {
  if (tok === "switzerland") return { level: "ch", id: "switzerland" };
  if (tok && tok.startsWith("region-") && REGIONS.some((r) => r.id === tok.slice(7))) return { level: "region", id: tok.slice(7) };
  if (CITIES.some((c) => c.id === tok)) return { level: "city", id: tok };
  return null;
}
const sc = () => parseScope(state.scope);
function scopeName(tok = state.scope) {
  const s = parseScope(tok);
  return s.level === "ch" ? "Switzerland" : s.level === "region" ? REGIONS.find((r) => r.id === s.id).name : cityOf(s.id).name;
}
function inScope(venueId, tok = state.scope) {
  const v = M.venues[venueId], s = parseScope(tok);
  if (s.level === "ch") return true;
  if (s.level === "region") return cityOf(v.city).region === s.id;
  return v.city === s.id;
}
const multiCity = () => sc().level !== "city";

/* ---------- routing: #<scope>[.<view>[.<param>]] ---------- */
const VIEWS = ["exhibitions", "events", "map", "tour", "favs", "venues", "artists", "about", "venue", "artist", "show"];
function hashFor(view = state.view, param = state.param, scope = state.scope) {
  let h = scope;
  if (view && view !== "exhibitions") h += "." + view;
  if (param) h += "." + param;
  return "#" + h;
}
function readHash() {
  const [tok, view, param] = decodeURIComponent(location.hash.slice(1)).split(".");
  state.scope = parseScope(tok) ? tok : (parseScope(state.scope) ? state.scope : "switzerland");
  store.set("scope", state.scope);
  let v = VIEWS.includes(view) ? view : "exhibitions";
  const lookup = { venue: M.venues, artist: M.artists, show: M.shows }[v];
  if (lookup && !lookup[param]) v = "exhibitions";
  state.view = v;
  state.param = lookup ? param : null;
}

/* ---------- shared helpers ---------- */
const artistNames = (x) => (x.artists.length ? x.artists.map((a) => M.artists[a].name).join(", ") : x.headline);
const artistLinks = (x) => x.artists.map((a) => `<a href="${hashFor("artist", a)}">${esc(M.artists[a].name)}</a>`).join(", ");
const showsAt = (venueId) => Object.values(M.shows).filter((x) => x.venue === venueId && isVisible(x)).sort((a, b) => a.start - b.start);
const hostOf = (url) => { try { return new URL(url).hostname.replace(/^www\./, ""); } catch { return ""; } };
function openLabel(v) {
  const o = isOpenNow(v);
  return o === true ? '<span class="openflag">Open now</span>' : o === false ? '<span class="mute sm">Closed now</span>' : "";
}
let toastTimer;
function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.textContent = ""; }, 2200);
}
const toggle = (list, id) => { const i = list.indexOf(id); i < 0 ? list.push(id) : list.splice(i, 1); return i < 0; };
const ageDays = () => Math.floor((Date.now() - M.generatedAt) / 864e5);
const staleNotice = () => (ageDays() >= 8 ? `<p class="notice"><b>Listings last updated ${ageDays()} days ago.</b> Some shows may have changed. Check the venue's website before you go.</p>` : "")
  + (loadedFromCache ? `<p class="notice"><b>You are offline or the listings could not be refreshed.</b> Showing the last saved copy.</p>` : "");

/* ---------- maps ---------- */
let map = null;
function destroyMap() { if (map) { try { map.destroy(); } catch { /* already gone */ } map = null; } }
function mountMap(opts = {}) {
  const el = $("#map");
  if (!el) return null;
  map = createMap(el, opts);
  return map;
}
const pinFor = (v, extra = {}) => ({ id: v.id, lat: v.lat, lon: v.lon, title: v.name, ...extra });

/* ---------- filters ---------- */
function filteredShows() {
  const q = state.q.trim().toLowerCase();
  return Object.values(M.shows).filter((x) => {
    if (!isVisible(x) || !inScope(x.venue)) return false;
    const v = M.venues[x.venue];
    if (state.type !== "all" && v.type !== state.type) return false;
    if (state.openNow && !(isCurrent(x) && isOpenNow(v) === true)) return false;
    if (q && !(x.title + " " + x.headline + " " + artistNames(x) + " " + v.name).toLowerCase().includes(q)) return false;
    return true;
  });
}
const byVenueThenStart = (a, b) => M.venues[a.venue].name.localeCompare(M.venues[b.venue].name, "de") || a.start - b.start;
function sections(list) {
  const d = (x) => diffDays(x.start, TODAY), e = (x) => diffDays(x.end, TODAY);
  return [
    ["Closing soon", list.filter(closingSoon).sort((a, b) => a.end - b.end)],
    ["Opening this week", list.filter((x) => d(x) >= 1 && d(x) <= 7).sort((a, b) => a.start - b.start)],
    ["On view", list.filter((x) => isCurrent(x) && e(x) > 7).sort(byVenueThenStart)],
    ["Coming up", list.filter((x) => d(x) > 7).sort((a, b) => a.start - b.start)],
  ].filter((s) => s[1].length);
}
function chipsHTML() {
  return `<button class="chip open" type="button" data-action="q-open" aria-pressed="${state.openNow}"><span class="dot"></span>Open now</button>
    <button class="chip" type="button" data-action="type" data-type="all" aria-pressed="${state.type === "all"}">All</button>
    ${TYPE_ORDER.map((t) => `<button class="chip" type="button" data-action="type" data-type="${t}" aria-pressed="${state.type === t}">${TYPES[t].short}</button>`).join("")}`;
}

/* ---------- cards ---------- */
function cardHTML(x, { showVenue = true } = {}) {
  const v = M.venues[x.venue], st = status(x), inTour = state.tour.includes(x.id), fav = state.favs.includes(x.id);
  const total = Math.max(1, diffDays(x.end, x.start)), done = Math.min(total, Math.max(0, diffDays(TODAY, x.start)));
  const run = x.noStart ? "" : `<span class="run" aria-hidden="true"><i style="width:${(done / total * 100).toFixed(1)}%"></i></span>`;
  let meta;
  if (st.c === "soon") meta = `<span class="status soon">${st.t}</span><span class="when">until ${fDate(x.end)}</span>${run}`;
  else if (st.c === "up") meta = `<span class="status up">${esc(st.t[0].toUpperCase() + st.t.slice(1))}</span><span class="when">${fDate(x.start)} – ${fDate(x.end)}</span>`;
  else meta = `<span class="when">${st.t}</span>${run}`;
  return `<article class="card" data-venue="${x.venue}">
    <a class="card-main" href="${hashFor("show", x.id)}">
      <div class="card-art">${esc(artistNames(x))}</div>
      ${x.title ? `<div class="card-title">${esc(x.title)}</div>` : ""}
      ${showVenue ? `<div class="card-venue">${esc(v.name)}${multiCity() ? " · " + esc(cityLabel(v.city)) : ""}</div>` : ""}
    </a>
    <div class="card-foot"><div class="meta">${meta}</div>
      <div class="acts">
        <button class="act" type="button" data-action="tour" data-id="${x.id}" aria-pressed="${inTour}" aria-label="${inTour ? "Remove from Tourplan" : "Add to Tourplan"}">${inTour ? I.check : I.plus}Plan</button>
        <button class="iconbtn" type="button" data-action="fav" data-id="${x.id}" aria-pressed="${fav}" aria-label="${fav ? "Remove from favourites" : "Save to favourites"}">${fav ? I.heartFill : I.heart}</button>
      </div></div>
  </article>`;
}

/* ================= views ================= */
const viewFns = {};

/* ----- shows ----- */
function resultsHTML() {
  const list = filteredShows();
  const secs = sections(list);
  let h = `<p class="resultline" aria-live="polite">${list.length} ${list.length === 1 ? "show" : "shows"} in ${esc(scopeName())}${state.q ? ` matching “${esc(state.q)}”` : ""}</p>`;
  h += staleNotice();
  if (!list.length) {
    h += `<p class="empty">${state.openNow ? `Nothing with known opening hours is open right now in ${esc(scopeName())}.` : "No shows match these filters."}</p>`;
  }
  secs.forEach(([title, items]) => {
    h += `<section class="group"><div class="gh"><h2>${title}</h2><span class="sm mute">${items.length} ${items.length === 1 ? "show" : "shows"}</span></div>${items.map((x) => cardHTML(x)).join("")}</section>`;
  });
  h += `<div class="browse"><a href="${hashFor("venues")}">Browse venues <span class="mute">${I.next}</span></a><a href="${hashFor("artists")}">Browse artists <span class="mute">${I.next}</span></a></div>`;
  return h;
}
function showsPins() {
  const byVenue = {};
  filteredShows().forEach((x) => { (byVenue[x.venue] ||= []).push(x); });
  return Object.entries(byVenue).map(([id, list]) => {
    const v = M.venues[id];
    return pinFor(v, {
      label: list.length, popup: `<b>${esc(v.name)}</b><br>${list.length} ${list.length === 1 ? "show" : "shows"} · ${esc(cityLabel(v.city))}<br><a href="${hashFor("venue", id)}">Venue page</a>`,
    });
  });
}
viewFns.exhibitions = () => ({
  html: `<div class="page"><div class="split hide-m">
    <section class="listcol" aria-label="Exhibitions">
      <div class="filterbar">
        <div class="search" role="search"><span aria-hidden="true">${I.search}</span><input type="search" id="q" placeholder="Search artist, title or venue" aria-label="Search shows" value="${esc(state.q)}" autocomplete="off"></div>
        <div class="chips" id="chips" role="group" aria-label="Filters">${chipsHTML()}</div>
      </div>
      <div id="results">${resultsHTML()}</div>
    </section>
    <aside class="mapcol" aria-label="Map of venues"><div class="map" id="map"></div></aside>
  </div></div>`,
  after() {
    if (!desktop.matches) return;
    if (mountMap({ wheel: true })) map.setPins(showsPins(), { click: onShowsPin });
  },
});
function updateShows({ pins = true } = {}) {
  $("#chips").innerHTML = chipsHTML();
  $("#results").innerHTML = resultsHTML();
  if (pins && map) map.setPins(showsPins(), { click: onShowsPin });
}
function onShowsPin(id) {
  const card = $(`#results .card[data-venue="${id}"]`);
  if (card) card.scrollIntoView({ behavior: "smooth", block: "center" });
}

/* ----- show detail ----- */
viewFns.show = () => {
  const x = M.shows[state.param], v = M.venues[x.venue], st = status(x), fav = state.favs.includes(x.id), inTour = state.tour.includes(x.id);
  const evs = M.events.filter((e) => e.show === x.id && diffDays(e.date, TODAY) >= 0).sort((a, b) => a.date - b.date);
  const more = showsAt(x.venue).filter((y) => y.id !== x.id);
  const pill = st.c === "soon" ? `<span class="status soon">${st.t}</span>` : st.c === "up" ? `<span class="status up">${esc(st.t[0].toUpperCase() + st.t.slice(1))}</span>` : "";
  const kind = TYPES[v.type].singular;
  return {
    html: `<div class="page"><div class="split">
      <article class="detail">
        <button class="back" type="button" data-action="back">${I.back} Back</button>
        <div class="page-h"><div class="kicker">${esc(kind)} · ${esc(cityLabel(v.city))}</div><h1>${esc(artistNames(x))}</h1>${x.title ? `<div class="sub">${esc(x.title)}</div>` : ""}</div>
        <div class="meta">${pill}<span class="when">${dateRange(x)}</span></div>
        <div class="btnrow">
          <button class="btn${inTour ? " on" : ""}" type="button" data-action="tour" data-id="${x.id}">${inTour ? I.check + " In Tourplan" : I.plus + " Add to Tourplan"}</button>
          <button class="btn ghost" type="button" data-action="fav" data-id="${x.id}" aria-pressed="${fav}">${fav ? I.heartFill + " Saved" : I.heart + " Save"}</button>
        </div>
        <dl class="kv"><dt>Venue</dt><dd><a href="${hashFor("venue", v.id)}"><b>${esc(v.name)}</b></a><br>${esc(v.address)}</dd>
          <dt>Hours</dt><dd>${isCurrent(x) ? openLabel(v) + "<br>" : ""}${esc(hoursText(v))}<br><span class="mute sm">As listed on the venue's website. Confirm with the venue.</span></dd>
          ${evs.length ? `<dt>Next</dt><dd><b>${evs[0].type}</b><br>${fDayLong(evs[0].date)}${evs[0].time ? ", " + evs[0].time : ""}</dd>` : ""}
          ${x.artists.length ? `<dt>Artists</dt><dd>${artistLinks(x)}</dd>` : ""}</dl>
        ${x.url ? `<p><a class="btn ghost" href="${esc(x.url)}" target="_blank" rel="noopener">Details on ${esc(hostOf(x.url) || "the venue's site")} ${I.ext}</a></p>` : ""}
        <div class="btnrow" aria-label="Calendar">
          ${x.noStart ? "" : `<a class="btn ghost" href="shows/${esc(x.id)}/run.ics" download>${I.cal} Add to calendar</a><a class="btn ghost" href="${esc(googleCal(x))}" target="_blank" rel="noopener">Google Calendar ${I.ext}</a>`}
          ${diffDays(x.end, TODAY) >= 0 ? `<a class="btn ghost" href="shows/${esc(x.id)}/closing.ics" download>${I.bell} Remind me before it closes</a>` : ""}
        </div>
        ${evs.length ? `<h2 class="sec-h">Events</h2>${evs.map(eventLine).join("")}` : ""}
        ${more.length ? `<h2 class="sec-h">Also at ${esc(v.name)}</h2>${more.map((y) => cardHTML(y, { showVenue: false })).join("")}` : ""}
      </article>
      <aside class="mapcol" aria-label="Map"><div class="map" id="map"></div></aside>
    </div></div>`,
    after() {
      if (mountMap()) map.setPins([pinFor(v, { label: "", selected: true, popup: `<b>${esc(v.name)}</b><br>${esc(v.address)}${v.approx ? "<br><span class='mute'>Position approximate</span>" : ""}` })]);
    },
  };
};
const ymd = (d) => `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;
function googleCal(x) {
  const v = M.venues[x.venue];
  const q = new URLSearchParams({ action: "TEMPLATE", text: `${artistNames(x)}${x.title ? ": " + x.title : ""} · ${v.name}`, dates: `${ymd(x.start)}/${ymd(addDays(x.end, 1))}`, details: x.url, location: `${v.name}, ${v.address}` });
  return "https://calendar.google.com/calendar/render?" + q;
}
const eventCal = (e) => (e.time ? `<br><a class="sm" href="events/${esc(e.id)}.ics" download>Add to calendar with reminder</a>` : "");
function eventLine(e) {
  return `<div class="vrow"><span><b>${fDayLong(e.date)}${e.time ? ", " + e.time : ""}</b><br><span class="mute sm">${esc(e.title)}</span>${eventCal(e)}</span><span><span class="tag t-${e.type}">${e.type}</span></span></div>`;
}

/* ----- events ----- */
viewFns.events = () => {
  const monday = addDays(TODAY, -((TODAY.getDay() + 6) % 7));
  const nowHM = new Date().toTimeString().slice(0, 5);
  const evs = M.events.filter((e) => inScope(e.venue) && (state.evType === "all" || e.typeId === state.evType) && diffDays(e.date, TODAY) >= 0 && e.date < addDays(monday, 28)
    && !(diffDays(e.date, TODAY) === 0 && e.time && e.time < nowHM));
  let h = `<div class="page"><div class="detail wide"><div class="page-h"><div class="kicker">${esc(scopeName())}</div><h1>Events</h1></div>
    ${staleNotice()}
    <p class="sm mute">Add events to your calendar with a reminder one hour before. <a href="calendar/events.ics" download>Calendar file with all events</a>. It lists everything, so add it once and delete what you don't want.</p>
    <div class="chips" role="group" aria-label="Event type"><button class="chip" type="button" data-action="evtype" data-type="all" aria-pressed="${state.evType === "all"}">All</button>
      ${EVENT_TYPES.map(([id, , plural]) => `<button class="chip" type="button" data-action="evtype" data-type="${id}" aria-pressed="${state.evType === id}">${plural}</button>`).join("")}</div>`;
  let any = false;
  for (let w = 0; w < 4; w++) {
    const ws = addDays(monday, w * 7);
    let days = "";
    for (let d = 0; d < 7; d++) {
      const day = addDays(ws, d);
      const list = evs.filter((e) => diffDays(e.date, day) === 0).sort((a, b) => a.time.localeCompare(b.time) || M.venues[a.venue].name.localeCompare(M.venues[b.venue].name));
      if (!list.length) continue;
      const dd = diffDays(day, TODAY);
      days += `<div class="day"><div class="day-d">${fWeekday(day)}<b>${day.getDate()}</b>${dd === 0 ? "<em>Today</em>" : dd === 1 ? "<em>Tomorrow</em>" : day.toLocaleDateString("en-GB", { month: "short" })}</div><div>` +
        list.map((e) => {
          const x = e.show && M.shows[e.show];
          const v = M.venues[e.venue];
          const link = e.url ? `<div class="sm"><a href="${esc(e.url)}" target="_blank" rel="noopener">${esc(hostOf(e.url))} ${I.ext}</a></div>` : "";
          return `<div class="ev"><span class="ev-t">${e.time || "–"}</span><div class="ev-x"><span class="tag t-${e.type}">${e.type}</span>
            ${x ? `<div><a href="${hashFor("show", x.id)}"><b>${esc(artistNames(x))}</b>${x.title ? `<br><i>${esc(x.title)}</i>` : ""}</a></div>` : ""}
            ${e.typeId !== "opening" && e.typeId !== "finissage" ? `<div><b>${esc(e.title)}</b></div>` : ""}
            <div class="v"><a href="${hashFor("venue", e.venue)}">${esc(v.name)}</a>${multiCity() ? " · " + esc(cityLabel(v.city)) : ""}</div>${link}${eventCal(e)}</div></div>`;
        }).join("") + "</div></div>";
    }
    if (!days) continue;
    any = true;
    h += `<h2 class="week-h"><span>${w === 0 ? "This week" : w === 1 ? "Next week" : "Week of " + fDate(ws)}</span><span class="mono">${fDate(ws)} – ${fDate(addDays(ws, 6))}</span></h2>${days}`;
  }
  if (!any) h += `<p class="empty">No events listed for this selection. Venues announce talks and openings close to the date, so check again soon.</p>`;
  return { html: h + "</div></div>" };
};

/* ----- map ----- */
function mapModel() {
  const list = filteredShows();
  const venues = [...new Set(list.map((x) => x.venue))].map((id) => M.venues[id]).sort((a, b) => a.name.localeCompare(b.name, "de"));
  if (!venues.some((v) => v.id === state.mapSel)) state.mapSel = venues[0] ? venues[0].id : null;
  const sel = state.mapSel && M.venues[state.mapSel];
  const idx = sel ? venues.indexOf(sel) + 1 : 0;
  const shows = sel ? list.filter((x) => x.venue === sel.id).sort((a, b) => a.start - b.start) : [];
  const dir = sel ? "https://www.google.com/maps/dir/?api=1&travelmode=walking&destination=" + encodeURIComponent(sel.name + ", " + sel.address) : "";
  return { list, venues, sel, idx, shows, dir };
}
viewFns.map = () => {
  const { list, venues, sel, idx, shows, dir } = mapModel();
  return {
    html: `<div class="page"><div class="split map-first-m">
      <section class="listcol" aria-label="Venues">
        <div class="page-h"><div class="kicker">${esc(scopeName())}</div><h1>Map</h1></div>
        <div class="filterbar"><div class="chips" id="chips" role="group" aria-label="Filters">${chipsHTML()}</div></div>
        ${venues.length ? `<div class="vsheet" id="vsheet">${vsheetHTML(sel, idx, shows, dir)}</div>
          <div class="legend" id="legend">${legendHTML(venues, list)}</div>` : `<p class="empty">No shows match these filters.</p>`}
      </section>
      <aside class="mapcol" aria-label="Map of venues"><div class="map" id="map"></div></aside>
    </div></div>`,
    after() {
      if (!mountMap({ wheel: true }) || !venues.length) return;
      map.setPins(venues.map((v, i) => pinFor(v, { label: i + 1, selected: v.id === state.mapSel })), { click: selectVenue });
    },
  };
};
function vsheetHTML(sel, idx, shows, dir) {
  const first = shows[0];
  return `<div class="vsheet-h"><span class="n">${idx}</span><div style="min-width:0"><b>${esc(sel.name)}</b><span class="sm mute">${esc(sel.address)} </span>${openLabel(sel)}</div></div>
    ${shows.map((x) => `<a class="minishow" href="${hashFor("show", x.id)}"><b>${esc(artistNames(x))}</b>${x.title ? `<br><i>${esc(x.title)}</i>` : ""}<div class="sm mute">${status(x).t}</div></a>`).join("")}
    <div class="btnrow" style="margin:0">${first ? `<button class="btn${state.tour.includes(first.id) ? " on" : ""}" type="button" data-action="tour" data-id="${first.id}">${state.tour.includes(first.id) ? I.check + " In Tourplan" : I.plus + " Add to Tourplan"}</button>` : ""}
      <a class="btn ghost" href="${dir}" target="_blank" rel="noopener">Directions ${I.ext}</a><a class="btn ghost" href="${hashFor("venue", sel.id)}">Venue</a></div>`;
}
function legendHTML(venues, list) {
  return venues.map((v, i) => {
    const n = list.filter((x) => x.venue === v.id).length;
    return `<button type="button" data-action="pin" data-id="${v.id}" aria-pressed="${state.mapSel === v.id}"><span class="num">${i + 1}</span><span>${esc(v.name)}</span><span class="mono mute">${n} ${n === 1 ? "show" : "shows"}</span></button>`;
  }).join("");
}
function selectVenue(id) {
  state.mapSel = id;
  const { list, venues, sel, idx, shows, dir } = mapModel();
  const sheet = $("#vsheet");
  if (!sheet || !sel) { render(); return; }
  sheet.innerHTML = vsheetHTML(sel, idx, shows, dir);
  $("#legend").innerHTML = legendHTML(venues, list);
  if (map) map.select(id);
}

/* ----- tourplan ----- */
const nearestOrder = (ids) => {
  if (ids.length < 3) return ids;
  const rest = ids.slice(1), out = [ids[0]];
  const d = (a, b) => { const A = M.venues[M.shows[a].venue], B = M.venues[M.shows[b].venue]; return Math.hypot(A.lat - B.lat, (A.lon - B.lon) * 0.68); };
  while (rest.length) {
    const last = out[out.length - 1];
    let bi = 0;
    rest.forEach((r, i) => { if (d(last, r) < d(last, rest[bi])) bi = i; });
    out.push(rest.splice(bi, 1)[0]);
  }
  return out;
};
const tourIds = () => {
  const ids = state.tour.filter((id) => M.shows[id]);
  return state.tourOrder === "shortest" ? nearestOrder(ids) : ids;
};
viewFns.tour = () => {
  const custom = state.tourOrder !== "shortest";
  const items = tourIds().map((id) => M.shows[id]);
  let h = `<div class="page"><div class="split map-first-m"><section class="listcol detail"><div class="page-h"><div class="kicker">Your route</div><h1>Tourplan</h1></div>`;
  if (!items.length) {
    return { html: h + `<p class="empty">Your Tourplan is empty. Tap <b>Plan</b> on any show to add it. Stops appear here in visiting order, with a route and walking times.</p><a class="btn ghost" href="${hashFor("exhibitions")}">Browse shows</a></section></div></div>` };
  }
  const legs = items.slice(1).map((x, i) => walkKm(M.venues[items[i].venue], M.venues[x.venue]));
  const total = legs.reduce((a, b) => a + b, 0), walkable = legs.every((k) => k <= 2.5);
  const places = items.map((x) => encodeURIComponent(M.venues[x.venue].name + ", " + M.venues[x.venue].address));
  const gmaps = items.length > 1
    ? `https://www.google.com/maps/dir/?api=1&travelmode=walking&origin=${places[0]}&destination=${places[places.length - 1]}${places.length > 2 ? "&waypoints=" + places.slice(1, -1).join("%7C") : ""}`
    : `https://www.google.com/maps/dir/?api=1&travelmode=walking&destination=${places[0]}`;
  h += `<p class="sm" style="margin:6px 0 0"><b>${items.length} ${items.length === 1 ? "stop" : "stops"}</b>${items.length > 1 ? ` · ${total.toFixed(1)} km${walkable ? `, about ${Math.round(total / 4.8 * 60)} min on foot` : ""}` : ""}<span class="mute"> · estimated</span></p>
    <div class="btnrow"><a class="btn" href="${gmaps}" target="_blank" rel="noopener">Open route in Google Maps ${I.ext}</a><button class="btn ghost" type="button" data-action="clear-tour">Clear</button></div>
    <div class="orderbox"><div class="sm mute" id="order-label">Order</div>
      <div class="seg" role="group" aria-labelledby="order-label"><button type="button" data-action="tour-order" data-mode="shortest" aria-pressed="${!custom}">Shortest order</button><button type="button" data-action="tour-order" data-mode="custom" aria-pressed="${custom}">Custom</button></div>
      <p class="sm mute" style="margin:0">${custom ? "Your own order. Use the arrows to move a stop." : "Starts at your first stop, then always goes to the nearest one next."}</p></div><div class="stops">`;
  items.forEach((x, i) => {
    const v = M.venues[x.venue];
    if (i > 0) { const k = legs[i - 1]; h += `<div class="walk"><i></i><span>${k <= 2.5 ? Math.max(1, Math.round(k / 4.8 * 60)) + " min walk" : k.toFixed(1) + " km, by tram or train"}</span></div>`; }
    h += `<div class="stop"><span class="n">${i + 1}</span><a class="stop-main" href="${hashFor("show", x.id)}"><b>${esc(v.name)}</b><span>${esc(artistNames(x))}${x.title ? ", <i>" + esc(x.title) + "</i>" : ""}</span>
      <div class="sm">${openLabel(v)} <span class="mute">· ${esc(hoursText(v))}</span></div></a>
      <span class="ctl">${custom ? `<button class="iconbtn" type="button" data-action="up" data-id="${x.id}" aria-label="Move up" ${i === 0 ? "disabled" : ""}>${I.up}</button><button class="iconbtn" type="button" data-action="down" data-id="${x.id}" aria-label="Move down" ${i === items.length - 1 ? "disabled" : ""}>${I.down}</button>` : ""}<button class="iconbtn" type="button" data-action="tour" data-id="${x.id}" aria-label="Remove">${I.x}</button></span></div>`;
  });
  h += `</div></section><aside class="mapcol" aria-label="Route map"><div class="map" id="map"></div></aside></div></div>`;
  return {
    html: h,
    after() {
      if (!mountMap({ wheel: true })) return;
      const pins = items.map((x, i) => pinFor(M.venues[x.venue], { id: x.id, label: i + 1, selected: true }));
      map.setPins(pins);
      map.setRoute(pins.map((p) => [p.lat, p.lon]));
    },
  };
};

/* ----- saved ----- */
viewFns.favs = () => {
  const items = state.favs.map((id) => M.shows[id]).filter((x) => x && isVisible(x));
  return { html: `<div class="page"><div class="detail wide"><div class="page-h"><div class="kicker">Saved shows</div><h1>Favourites</h1></div>
    ${items.length ? items.map((x) => cardHTML(x)).join("") : `<p class="empty">No favourites yet. Tap the heart on a show to keep it here. Favourites stay on this device.</p>`}</div></div>` };
};

/* ----- venues ----- */
viewFns.venues = () => {
  const q = state.venueQ.toLowerCase();
  const base = Object.values(M.venues).filter((v) => inScope(v.id) && (!q || (v.name + " " + v.address).toLowerCase().includes(q)) && (!state.venueOpen || isOpenNow(v) === true));
  const vs = base.filter((v) => state.venueType === "all" || v.type === state.venueType);
  const chip = (t, l, n) => `<button class="chip" type="button" data-action="vtype" data-type="${t}" aria-pressed="${state.venueType === t}" ${n ? "" : "disabled"}>${l} <span class="mono">${n}</span></button>`;
  let h = `<div class="page"><div class="detail wide"><div class="page-h"><div class="kicker">${esc(scopeName())}</div><h1>Venues</h1></div>
    <div class="filterbar"><div class="search" role="search"><span aria-hidden="true">${I.search}</span><input type="search" id="vq" placeholder="Search venues" aria-label="Search venues" value="${esc(state.venueQ)}" autocomplete="off"></div>
    <div class="chips" role="group" aria-label="Venue type">${chip("all", "All", base.length)}${TYPE_ORDER.map((t) => chip(t, TYPES[t].short, base.filter((v) => v.type === t).length)).join("")}
      <button class="chip open" type="button" data-action="vopen" aria-pressed="${state.venueOpen}"><span class="dot"></span>Open now</button></div></div><div id="vlist">${venueListHTML(vs)}</div></div></div>`;
  return { html: h };
};
function venueListHTML(vs) {
  if (!vs.length) return `<p class="empty">No venues match.</p>`;
  return TYPE_ORDER.map((t) => {
    const list = vs.filter((v) => v.type === t).sort((a, b) => a.name.localeCompare(b.name, "de"));
    if (!list.length) return "";
    return `<section class="group"><div class="gh"><h2>${TYPES[t].name}</h2><span class="mono mute">${list.length}</span></div>${list.map((v) => {
      const n = showsAt(v.id).length;
      return `<a class="vrow" href="${hashFor("venue", v.id)}"><span class="nm">${esc(v.name)}</span><span class="ct">${n} ${n === 1 ? "show" : "shows"}</span>
        <span class="ad">${esc(v.address)}</span><span>${isOpenNow(v) === true ? '<span class="openflag">● open</span>' : ""}</span></a>`;
    }).join("")}</section>`;
  }).join("");
}
viewFns.venue = () => {
  const v = M.venues[state.param], shows = showsAt(v.id);
  const evs = M.events.filter((e) => e.venue === v.id && diffDays(e.date, TODAY) >= 0).sort((a, b) => a.date - b.date);
  const dir = "https://www.google.com/maps/dir/?api=1&travelmode=walking&destination=" + encodeURIComponent(v.name + ", " + v.address);
  return {
    html: `<div class="page"><div class="split">
      <article class="detail"><a class="back" href="${hashFor("venues")}">${I.back} Venues</a>
        <div class="page-h"><div class="kicker">${esc(TYPES[v.type].singular)} · ${esc(cityLabel(v.city))}</div><h1>${esc(v.name)}</h1></div>
        <dl class="kv"><dt>Address</dt><dd>${esc(v.address)}<br><a href="${dir}" target="_blank" rel="noopener">Walking directions ↗</a>${v.approx ? '<br><span class="mute sm">Map position is approximate.</span>' : ""}</dd>
          <dt>Hours</dt><dd>${openLabel(v)} ${esc(hoursText(v))}<br><span class="mute sm">As listed on the venue's website. Confirm with the venue.</span></dd>
          <dt>Website</dt><dd>${v.site ? `<a href="${esc(v.site)}" target="_blank" rel="noopener">${esc(v.web)} ↗</a>` : '<span class="mute">Not listed</span>'}</dd></dl>
        <h2 class="sec-h">Current &amp; upcoming</h2>${shows.length ? shows.map((x) => cardHTML(x, { showVenue: false })).join("") : `<p class="empty">No shows listed right now. Check the venue's website.</p>`}
        ${evs.length ? `<h2 class="sec-h">Events</h2>${evs.map(eventLine).join("")}` : ""}
      </article>
      <aside class="mapcol" aria-label="Map"><div class="map" id="map"></div></aside></div></div>`,
    after() { if (mountMap()) map.setPins([pinFor(v, { label: "", selected: true, popup: `<b>${esc(v.name)}</b><br>${esc(v.address)}` })]); },
  };
};

/* ----- artists ----- */
viewFns.artists = () => {
  const q = state.artistQ.toLowerCase();
  const ids = Object.keys(M.artists).filter((a) => Object.values(M.shows).some((x) => x.artists.includes(a) && isVisible(x) && inScope(x.venue)) && (!q || M.artists[a].name.toLowerCase().includes(q)))
    .sort((a, b) => M.artists[a].sort.localeCompare(M.artists[b].sort, "de"));
  const letter = (a) => M.artists[a].sort[0].toUpperCase().normalize("NFD")[0];
  const letters = [...new Set(ids.map(letter))];
  let h = `<div class="page"><div class="detail wide"><div class="page-h"><div class="kicker">${esc(scopeName())} · ${ids.length} artists</div><h1>Artists</h1></div>
    <div class="filterbar"><div class="search" role="search"><span aria-hidden="true">${I.search}</span><input type="search" id="aq" placeholder="Search artists" aria-label="Search artists" value="${esc(state.artistQ)}" autocomplete="off"></div></div>
    <div id="alist">`;
  if (!ids.length) h += `<p class="empty">No artists match.</p>`;
  if (letters.length > 1) h += `<nav class="alpha" aria-label="Jump to letter">${letters.map((l) => `<a href="#" data-action="jump" data-l="${l}">${l}</a>`).join("")}</nav>`;
  letters.forEach((l) => {
    h += `<h2 class="letter" id="L-${l}">${l}</h2>`;
    ids.filter((a) => letter(a) === l).forEach((a) => {
      const shows = Object.values(M.shows).filter((x) => x.artists.includes(a) && isVisible(x));
      const cities = [...new Set(shows.map((x) => cityOf(M.venues[x.venue].city).name))];
      h += `<a class="vrow" href="${hashFor("artist", a)}"><span class="nm">${esc(M.artists[a].name)}</span><span class="ct">${shows.length} ${shows.length === 1 ? "show" : "shows"}</span><span class="ad">${esc(cities.join(", "))}</span><span></span></a>`;
    });
  });
  return { html: h + "</div></div></div>" };
};
viewFns.artist = () => {
  const a = M.artists[state.param];
  const shows = Object.values(M.shows).filter((x) => x.artists.includes(a.id) && isVisible(x)).sort((x, y) => x.start - y.start);
  return { html: `<div class="page"><div class="detail wide"><a class="back" href="${hashFor("artists")}">${I.back} Artists</a>
    <div class="page-h"><div class="kicker">Artist</div><h1>${esc(a.name)}</h1></div>
    <p class="mute sm">All current and upcoming shows across Switzerland, whatever location you have selected.</p>
    <h2 class="sec-h">Shows</h2>${shows.map((x) => cardHTML(x)).join("") || '<p class="empty">No shows listed.</p>'}</div></div>` };
};

/* ----- about ----- */
viewFns.about = () => ({
  html: `<div class="page"><div class="detail"><div class="page-h"><div class="kicker">About</div><h1>Weekly VERNI</h1></div>
    <div class="prose"><p>Weekly VERNI lists exhibitions, openings and events at galleries, museums, foundations and off-spaces across Switzerland.</p>
    <p>Pick Switzerland, a region or a single city at the top. Every page follows that choice.</p>
    <p>Everything here comes from the venues' own websites, and each show links back to its source. The listings are re-read twice a week. Venues change their programme often, so confirm dates and hours with the venue before you go.</p>
    <p>Some venues are missing or incomplete, mostly where a website could not be read automatically. They are added as soon as their pages can be read.</p></div>
    <dl class="kv"><dt>Updated</dt><dd>${M.generatedAt.toLocaleString("en-GB", { dateStyle: "long", timeStyle: "short" })}</dd>
      <dt>Venues</dt><dd>${Object.keys(M.venues).length}</dd><dt>Shows</dt><dd>${Object.keys(M.shows).length}</dd><dt>Events</dt><dd>${M.events.length}</dd>
      <dt>Maps</dt><dd>© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors</dd></dl></div></div>`,
});

/* ================= chrome ================= */
const NAV = [["exhibitions", "Shows", I.list], ["events", "Events", I.cal], ["map", "Map", I.pin], ["tour", "Plan", I.route]];
const DESKTOP_TABS = [...NAV.map(([id, l]) => [id, l]), ["venues", "Venues"], ["artists", "Artists"]];
function updateChrome() {
  $("#scope-btn").innerHTML = `${I.pinS}<span>${esc(scopeName())}</span>${I.chev}`;
  $("#scope-btn").setAttribute("aria-label", `Location: ${scopeName()}. Change location`);
  const n = state.favs.filter((id) => M.shows[id]).length;
  const c = $("#saved-count");
  c.textContent = n;
  c.hidden = !n;
  $("#saved-link").href = hashFor("favs", null);
  $("#brand").href = hashFor("exhibitions", null);
  const active = { show: "exhibitions", venue: "venues", artist: "artists" }[state.view] || state.view;
  $("#tabs").innerHTML = DESKTOP_TABS.map(([id, l]) => `<a href="${hashFor(id, null)}" ${active === id ? 'aria-current="page"' : ""}>${l}</a>`).join("");
  const tourN = state.tour.filter((id) => M.shows[id]).length;
  $("#bottom").innerHTML = NAV.map(([id, l, ic]) => `<a href="${hashFor(id, null)}" ${active === id ? 'aria-current="page"' : ""}><span class="ic">${ic}${id === "tour" && tourN ? `<span class="badge">${tourN}</span>` : ""}</span>${l}</a>`).join("");
  const titles = { exhibitions: "", events: "Events · ", map: "Map · ", tour: "Tourplan · ", favs: "Favourites · ", venues: "Venues · ", artists: "Artists · ", about: "About · " };
  let t = titles[state.view] ?? "";
  if (state.view === "show") t = artistNames(M.shows[state.param]) + " · ";
  if (state.view === "venue") t = M.venues[state.param].name + " · ";
  if (state.view === "artist") t = M.artists[state.param].name + " · ";
  document.title = t + "Weekly VERNI";
  document.documentElement.style.setProperty("--header-h", $("#top").offsetHeight + "px");
  $("#foot").innerHTML = `<nav aria-label="Footer"><a href="${hashFor("venues")}">Venues</a><a href="${hashFor("artists")}">Artists</a><a href="${hashFor("about")}">About</a></nav>
    <span>Listings gathered from the venues' own websites, updated ${M.generatedAt.toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}. Confirm dates and hours with the venue. Map © OpenStreetMap contributors. English only for now.</span>`;
}

function render() {
  destroyMap();
  const view = viewFns[state.view]();
  const main = $("#main");
  main.innerHTML = view.html;
  updateChrome();
  if (view.after) view.after();
}

/* ================= dialogs ================= */
const dlg = $("#dlg");
function openDialog(html) {
  dlg.innerHTML = `<div class="dlg-in">${html}</div>`;
  if (!dlg.open) dlg.showModal();
}
function closeDialog() { if (dlg.open) dlg.close(); }
dlg.addEventListener("click", (e) => { if (e.target === dlg) closeDialog(); });
function scopeDialog() {
  const count = (tok) => Object.values(M.shows).filter((x) => isVisible(x) && inScope(x.venue, tok)).length;
  let h = `<div class="dlg-h"><h2>Location</h2><button class="done" type="button" data-action="close">Done</button></div>
    <input type="search" id="sc-q" placeholder="Search city or region" aria-label="Search city or region" autocomplete="off">
    <div id="sc-sw"><button class="opt" type="button" data-action="set-scope" data-scope="switzerland" aria-current="${state.scope === "switzerland"}"><span><span class="nm">Switzerland</span><span class="smx">Everything, grouped by city</span></span><span class="ct">${count("switzerland")}</span></button></div>
    <div class="lvl-h">Regions</div>`;
  REGIONS.forEach((r) => {
    const tok = "region-" + r.id;
    h += `<div class="rg" data-rname="${esc((r.name + " " + r.note).toLowerCase())}"><button class="opt" type="button" data-action="set-scope" data-scope="${tok}" aria-current="${state.scope === tok}"><span><span class="nm">${esc(r.name)}</span><span class="smx">${esc(r.note)}</span></span><span class="ct">${count(tok)}</span></button>
      <div class="cities">${CITIES.filter((c) => c.region === r.id).map((c) => { const n = count(c.id); return `<button type="button" data-action="set-scope" data-scope="${c.id}" aria-current="${state.scope === c.id}" ${n ? "" : "disabled"}>${esc(cityLabel(c.id))} <span class="mono">${n}</span></button>`; }).join("")}</div></div>`;
  });
  openDialog(h);
}
function filterScope(q) {
  q = q.trim().toLowerCase();
  dlg.querySelectorAll(".rg").forEach((rg) => {
    const whole = !q || rg.dataset.rname.includes(q);
    let any = whole;
    rg.querySelectorAll(".cities button").forEach((b) => { const show = whole || b.textContent.toLowerCase().includes(q); b.hidden = !show; if (show) any = true; });
    rg.hidden = !any;
  });
  $("#sc-sw").hidden = !!q && !"switzerland everything country".includes(q);
}
function menuDialog() {
  openDialog(`<div class="dlg-h"><h2>Weekly VERNI</h2><button class="done" type="button" data-action="close">Done</button></div>
    <nav class="menu" aria-label="Menu"><div class="grp">Browse</div><a href="${hashFor("venues")}">Venues</a><a href="${hashFor("artists")}">Artists</a>
    <div class="grp">More</div><a href="${hashFor("about")}">About</a><button type="button" data-action="reset">Clear Tourplan &amp; Favourites</button></nav>`);
}

/* ================= interaction ================= */
const LIST_VIEWS = ["exhibitions", "venue", "artist"];
/* Update the Plan and heart buttons of a card in place, so keyboard focus stays where it was.
   Pages where the list itself changes (Tourplan, Favourites, detail pages) are redrawn instead. */
function syncButtons(id, clicked) {
  updateChrome();
  const card = clicked.closest(".card");
  if (!card || !LIST_VIEWS.includes(state.view)) { render(); return; }
  document.querySelectorAll(`.card [data-id="${id}"]`).forEach((b) => {
    if (b.dataset.action === "tour") {
      const on = state.tour.includes(id);
      b.setAttribute("aria-pressed", on);
      b.setAttribute("aria-label", on ? "Remove from Tourplan" : "Add to Tourplan");
      b.innerHTML = (on ? I.check : I.plus) + "Plan";
    } else if (b.dataset.action === "fav") {
      const on = state.favs.includes(id);
      b.setAttribute("aria-pressed", on);
      b.setAttribute("aria-label", on ? "Remove from favourites" : "Save to favourites");
      b.innerHTML = on ? I.heartFill : I.heart;
    }
  });
}
function refresh() { state.view === "exhibitions" ? (updateShows(), updateChrome()) : render(); }
const persist = () => { store.set("tour", state.tour); store.set("favs", state.favs); store.set("tourOrder", state.tourOrder); };

document.addEventListener("click", (e) => {
  const a = e.target.closest("[data-action]");
  if (!a) return;
  const act = a.dataset.action, id = a.dataset.id;
  if (a.tagName === "A") e.preventDefault();
  switch (act) {
    case "close": closeDialog(); break;
    case "back": if (history.length > 1) history.back(); else location.hash = hashFor("exhibitions", null); break;
    case "set-scope": {
      closeDialog(); state.mapSel = null;
      const keep = ["venue", "artist", "show"].includes(state.view) ? "exhibitions" : state.view;
      location.hash = hashFor(keep, null, a.dataset.scope);
      toast("Showing " + scopeName(a.dataset.scope));
      break;
    }
    case "q-open": state.openNow = !state.openNow; refresh(); break;
    case "type": state.type = a.dataset.type; refresh(); break;
    case "tour": { const added = toggle(state.tour, id); persist(); syncButtons(id, a); toast(added ? `Added to Tourplan (${state.tour.length})` : "Removed from Tourplan"); break; }
    case "fav": { const added = toggle(state.favs, id); persist(); syncButtons(id, a); toast(added ? "Saved to Favourites" : "Removed from Favourites"); break; }
    case "up": case "down": {
      const ids = state.tour.filter((t) => M.shows[t]);
      const i = ids.indexOf(id), j = act === "up" ? i - 1 : i + 1;
      [ids[i], ids[j]] = [ids[j], ids[i]];
      state.tour = ids; persist(); render(); break;
    }
    case "tour-order": state.tourOrder = a.dataset.mode === "shortest" ? "shortest" : "custom"; persist(); render(); break;
    case "clear-tour": state.tour = []; persist(); render(); break;
    case "reset": state.tour = []; state.favs = []; persist(); closeDialog(); render(); toast("Cleared"); break;
    case "pin": selectVenue(id); break;
    case "vtype": state.venueType = a.dataset.type; render(); break;
    case "vopen": state.venueOpen = !state.venueOpen; render(); break;
    case "evtype": state.evType = a.dataset.type; render(); break;
    case "jump": { const t = document.getElementById("L-" + a.dataset.l); if (t) t.scrollIntoView({ behavior: "smooth", block: "start" }); break; }
    default: break;
  }
});
$("#scope-btn").addEventListener("click", scopeDialog);
$("#menu-btn").addEventListener("click", menuDialog);
let searchTimer;
document.addEventListener("input", (e) => {
  const t = e.target;
  if (t.id === "q") { state.q = t.value; clearTimeout(searchTimer); searchTimer = setTimeout(() => { if (state.view === "exhibitions") updateShows(); }, 140); }
  if (t.id === "vq") { state.venueQ = t.value; $("#vlist").innerHTML = venueListHTML(Object.values(M.venues).filter((v) => inScope(v.id) && (!state.venueQ || (v.name + " " + v.address).toLowerCase().includes(state.venueQ.toLowerCase())) && (state.venueType === "all" || v.type === state.venueType) && (!state.venueOpen || isOpenNow(v) === true))); }
  if (t.id === "aq") { state.artistQ = t.value; const keep = t.selectionStart; render(); const el = $("#aq"); el.focus(); el.setSelectionRange(keep, keep); }
  if (t.id === "sc-q") filterScope(t.value);
});
// hovering a card highlights its pin on laptops
document.addEventListener("mouseover", (e) => {
  if (!map || state.view !== "exhibitions") return;
  const c = e.target.closest(".card[data-venue]");
  if (c) map.select(c.dataset.venue, { pan: false });
});
window.addEventListener("hashchange", () => {
  const prev = state.view + state.param;
  readHash(); closeDialog(); render();
  if (prev !== state.view + state.param) window.scrollTo(0, 0);
});
desktop.addEventListener("change", () => { if (M) render(); });

/* A tab left open for hours would show yesterday's "today". Reload the listings when it comes back after a long idle. */
let hiddenAt = 0;
document.addEventListener("visibilitychange", () => {
  if (document.hidden) { hiddenAt = Date.now(); return; }
  if (hiddenAt && Date.now() - hiddenAt > 3 * 3600e3) location.reload();
});
window.addEventListener("resize", () => { if (M) document.documentElement.style.setProperty("--header-h", $("#top").offsetHeight + "px"); });

/* ================= start ================= */
async function start() {
  try {
    const { set, fromCache } = await loadListings();
    M = buildModel(set);
    loadedFromCache = fromCache;
  } catch {
    $("#main").innerHTML = `<div class="page"><div class="page-h"><h1>Listings unavailable</h1></div><p class="empty">The listings could not be loaded. Check your connection and try again.</p><button class="btn" type="button" id="retry">Try again</button></div>`;
    $("#retry").addEventListener("click", () => location.reload());
    return;
  }
  state.tour = state.tour.filter((id) => typeof id === "string");
  readHash();
  render();
}
start();
