// Loads data/shows.json and turns it into the objects the site uses. No content is invented here:
// everything shown comes from that file, which is gathered from the venues' own websites.

export const REGIONS = [
  { id: "basel", name: "Basel Region", note: "Basel, Riehen, Münchenstein, Liestal, Weil am Rhein, Saint-Louis, Lörrach" },
  { id: "zurich", name: "Zurich Region", note: "Zurich, Winterthur" },
  { id: "lake-geneva", name: "Lake Geneva", note: "Geneva, Lausanne, Vevey" },
  { id: "bern", name: "Bern", note: "Bern" },
  { id: "central", name: "Central Switzerland", note: "Lucerne" },
  { id: "ticino", name: "Ticino", note: "Lugano" },
];

export const CITIES = [
  { id: "basel", name: "Basel", region: "basel" },
  { id: "riehen", name: "Riehen", region: "basel" },
  { id: "muenchenstein", name: "Münchenstein", region: "basel" },
  { id: "liestal", name: "Liestal", region: "basel" },
  { id: "weil", name: "Weil am Rhein", region: "basel", cc: "DE" },
  { id: "stlouis", name: "Saint-Louis", region: "basel", cc: "FR" },
  { id: "loerrach", name: "Lörrach", region: "basel", cc: "DE" },
  { id: "zurich", name: "Zurich", region: "zurich" },
  { id: "winterthur", name: "Winterthur", region: "zurich" },
  { id: "geneva", name: "Geneva", region: "lake-geneva" },
  { id: "lausanne", name: "Lausanne", region: "lake-geneva" },
  { id: "vevey", name: "Vevey", region: "lake-geneva" },
  { id: "bern", name: "Bern", region: "bern" },
  { id: "lucerne", name: "Lucerne", region: "central" },
  { id: "lugano", name: "Lugano", region: "ticino" },
  { id: "nyon", name: "Nyon", region: "lake-geneva" },
  { id: "baden", name: "Baden", region: "zurich" },
  { id: "solothurn", name: "Solothurn", region: "bern" },
  { id: "locarno", name: "Locarno", region: "ticino" },
  { id: "neuchatel", name: "Neuchâtel", region: "bern" },
];

export const FESTIVAL_KINDS = [
  ["film", "Film"], ["media-art", "Media art"], ["photography", "Photography"], ["performance", "Performance"], ["art-week", "Art weeks"], ["other", "Other"],
];
export const festivalKindLabel = (k) => (FESTIVAL_KINDS.find(([id]) => id === k) || [0, "Festival"])[1];

export const TYPES = {
  gallery: { name: "Galleries", short: "Galleries", singular: "Gallery" },
  institution: { name: "Institutions", short: "Institutions", singular: "Institution" },
  foundation: { name: "Foundations & Private Collections", short: "Foundations", singular: "Foundation / private collection" },
  offspace: { name: "Off-spaces", short: "Off-spaces", singular: "Off-space" },
};
export const TYPE_ORDER = ["gallery", "institution", "foundation", "offspace"];

export const EVENT_TYPES = [
  ["opening", "Opening", "Openings"],
  ["finissage", "Finissage", "Finissages"],
  ["talk", "Talk", "Talks"],
  ["tour", "Tour", "Tours"],
  ["performance", "Performance", "Performances"],
];
const EVENT_LABEL = Object.fromEntries(EVENT_TYPES.map(([id, one]) => [id, one]));

export const cityOf = (id) => CITIES.find((c) => c.id === id) || CITIES[0];
export const cityLabel = (id) => { const c = cityOf(id); return c.name + (c.cc ? ` (${c.cc})` : ""); };

// ---- dates ----
const DAY = 864e5;
export const TODAY = (() => { const d = new Date(); d.setHours(0, 0, 0, 0); return d; })();
export const addDays = (d, n) => { const r = new Date(d); r.setDate(r.getDate() + n); return r; };
export const diffDays = (a, b) => Math.round((a - b) / DAY);
const fmt = (d, o) => d.toLocaleDateString("en-GB", o);
export const fDate = (d) => fmt(d, { day: "numeric", month: "short" });
export const fDateY = (d) => fmt(d, { day: "numeric", month: "short", year: "numeric" });
export const fWeekday = (d) => fmt(d, { weekday: "short" });
export const fDayLong = (d) => fmt(d, { weekday: "short", day: "numeric", month: "short" });
// Links come from scraped data, so only plain web addresses are allowed through.
export const safeUrl = (u) => { try { const x = new URL(u); return x.protocol === "https:" || x.protocol === "http:" ? x.href : ""; } catch { return ""; } };
const isoDay = (s) => { const [y, m, d] = s.split("-").map(Number); return new Date(y, m - 1, d); };

// ---- loading ----
const CACHE_KEY = "verni:listings";

export async function loadListings() {
  try {
    const res = await fetch("data/shows.json", { cache: "no-cache" });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const set = await res.json();
    validate(set);
    try { localStorage.setItem(CACHE_KEY, JSON.stringify(set)); } catch { /* storage may be unavailable */ }
    return { set, fromCache: false };
  } catch (err) {
    try {
      const cached = JSON.parse(localStorage.getItem(CACHE_KEY) || "null");
      if (cached) { validate(cached); return { set: cached, fromCache: true }; }
    } catch { /* ignore */ }
    throw err;
  }
}

function validate(set) {
  if (!set || set.schemaVersion !== 1 || !Array.isArray(set.venues) || !Array.isArray(set.shows) || !Array.isArray(set.events)) {
    throw new Error("Unexpected data format");
  }
}

// ---- model ----
const slug = (n) => n.normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const sortKey = (n) => {
  const p = n.split(" ");
  return (p.length > 1 && !/Kollektiv|\//.test(n) ? p.slice(1).join(" ") + " " + p[0] : n).toLowerCase();
};

export function buildModel(set) {
  const venues = {};
  for (const v of set.venues) {
    let host = "";
    try { host = new URL(v.website).hostname.replace(/^www\./, ""); } catch { /* no website */ }
    venues[v.id] = {
      id: v.id, name: v.name, type: v.type, city: v.city, address: v.address,
      site: safeUrl(v.website), web: host, lat: v.lat, lon: v.lon, approx: !!v.geoApprox,
      hours: (v.hours || []).map((h) => ({ d: h.days, o: h.open, c: h.close })), source: safeUrl(v.sourceURL || v.website),
    };
  }
  const artists = {};
  const shows = {};
  for (const s of set.shows) {
    if (!venues[s.venue] || !s.end || !Array.isArray(s.artists)) continue;
    const ids = s.artists.map((name) => {
      const id = slug(name);
      if (!artists[id]) artists[id] = { id, name, sort: sortKey(name) };
      return id;
    });
    const sameAsArtist = ids.length && s.title === s.artists.join(", ");
    shows[s.id] = {
      id: s.id, venue: s.venue, artists: ids,
      title: ids.length && !sameAsArtist ? s.title : "", headline: s.title,
      start: s.start ? isoDay(s.start) : addDays(TODAY, -1), noStart: !s.start, end: isoDay(s.end), url: safeUrl(s.url),
    };
  }
  const events = set.events.filter((e) => venues[e.venue]).map((e) => ({
    id: e.id, date: isoDay(e.date), time: e.time || "", type: EVENT_LABEL[e.type] || "Talk", typeId: e.type,
    title: e.title, venue: e.venue, show: e.show && shows[e.show] ? e.show : null, url: safeUrl(e.url),
  }));
  const festivals = {};
  for (const f of set.festivals || []) {
    if (!f.id || !f.start || !f.end || !f.name) continue;
    festivals[f.id] = { id: f.id, name: f.name, kind: f.kind || "other", city: f.city, place: f.place || cityOf(f.city).name, lat: f.lat, lon: f.lon,
      start: isoDay(f.start), end: isoDay(f.end), url: safeUrl(f.url) };
  }
  return { venues, artists, shows, events, festivals, generatedAt: new Date(set.generatedAt) };
}

// ---- show helpers ----
export function status(x) {
  const toStart = diffDays(x.start, TODAY), left = diffDays(x.end, TODAY);
  if (toStart > 0) return { t: toStart === 1 ? "starts tomorrow" : "starts " + fDate(x.start), c: "up" };
  if (left === 0) return { t: "last day", c: "soon" };
  if (left <= 7) return { t: left + (left === 1 ? " day left" : " days left"), c: "soon" };
  return { t: "until " + fDate(x.end), c: "" };
}
export const isVisible = (x) => diffDays(x.end, TODAY) >= 0 && diffDays(x.start, TODAY) <= 35;
export const isCurrent = (x) => diffDays(x.start, TODAY) <= 0 && diffDays(x.end, TODAY) >= 0;
export const closingSoon = (x) => isCurrent(x) && diffDays(x.end, TODAY) <= 7;
export const festivalRange = (f) => (f.start.getFullYear() === f.end.getFullYear() ? fDate(f.start) : fDateY(f.start)) + " – " + fDateY(f.end);
export const dateRange = (x) => (x.noStart ? "until " + fDateY(x.end) : (x.start.getFullYear() === x.end.getFullYear() ? fDate(x.start) : fDateY(x.start)) + " – " + fDateY(x.end));

// ---- opening hours, in Swiss time. null when the venue's page did not state any ----
function zurichNow() {
  try {
    const p = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/Zurich", weekday: "short", hour: "2-digit", minute: "2-digit", hour12: false }).formatToParts(new Date());
    const g = (t) => p.find((x) => x.type === t).value;
    return { wd: { Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6, Sun: 7 }[g("weekday")], h: (+g("hour")) % 24 + (+g("minute")) / 60 };
  } catch {
    const d = new Date();
    return { wd: (d.getDay() + 6) % 7 + 1, h: d.getHours() + d.getMinutes() / 60 };
  }
}
export function isOpenNow(v) {
  if (!v.hours.length) return null;
  const n = zurichNow();
  return v.hours.some((s) => s.d.includes(n.wd) && n.h >= s.o && n.h < s.c);
}
export function hoursText(v) {
  if (!v.hours.length) return "See the venue's website";
  const D = ["", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const clock = (h) => { const w = Math.floor(h), m = Math.round((h - w) * 60); return m ? `${w}:${String(m).padStart(2, "0")}` : String(w); };
  const range = (a) => {
    a = [...a].sort((x, y) => x - y);
    const out = []; let s = a[0], p = a[0];
    for (let i = 1; i <= a.length; i++) {
      if (a[i] === p + 1) { p = a[i]; continue; }
      out.push(s === p ? D[s] : `${D[s]}–${D[p]}`);
      s = p = a[i];
    }
    return out.join(", ");
  };
  return v.hours.map((s) => `${range(s.d)} ${clock(s.o)}–${clock(s.c)}`).join(" · ");
}

// distance in km with a detour factor, for rough walking times
export function walkKm(a, b) {
  const t = Math.PI / 180, dLat = (b.lat - a.lat) * t, dLon = (b.lon - a.lon) * t;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * t) * Math.cos(b.lat * t) * Math.sin(dLon / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(h)) * 1.3;
}
