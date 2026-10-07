#!/usr/bin/env python3
"""Review tool: say yes or no to everything the discovery agent found, then publish.

    python3 tools/curate.py          # opens http://127.0.0.1:8123 in your browser

Candidates live in data/candidates.json (written by the agent, kept on your Mac, never published).
Yes  -> the record is added to data/shows.json.
No   -> it is remembered in data/rejected.json so it is not proposed again.
Publish -> validates, rebuilds the site pages, commits and pushes. Nothing goes live before you press it.

The server only answers on 127.0.0.1 and every request must carry a one-time token, so other websites cannot drive it."""
import datetime as dt, json, os, re, secrets, subprocess, sys, threading, unicodedata, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA, CANDS, REJECTED = ROOT / "data" / "shows.json", ROOT / "data" / "candidates.json", ROOT / "data" / "rejected.json"
TOKEN = secrets.token_urlsafe(16)
UNDO = []          # snapshots of the three files before each decision
LOCK = threading.Lock()


def read(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def write(path, obj):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def slug(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:56] or "item"


def key_of(c):
    r = c.get("record", {})
    return f"{c.get('kind')}|{slug(r.get('name') or r.get('title') or ' '.join(r.get('artists', [])))}|{r.get('start') or r.get('date') or ''}"


def state():
    data, cands, rej = read(DATA, {}), read(CANDS, {"candidates": []}), read(REJECTED, {"rejected": []})
    seen = {r["key"] for r in rej["rejected"]}
    pending = [c for c in cands["candidates"] if key_of(c) not in seen]
    git = subprocess.run(["git", "status", "--porcelain", "data/shows.json"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return {"candidates": pending, "venues": [{"id": v["id"], "name": v["name"], "city": v["city"]} for v in data.get("venues", [])],
            "cities": sorted({v["city"] for v in data.get("venues", [])} | {f["city"] for f in data.get("festivals", [])} | {"nyon", "baden", "solothurn", "locarno", "neuchatel"}),
            "counts": {"festivals": len(data.get("festivals", [])), "shows": len(data.get("shows", [])), "events": len(data.get("events", [])), "rejected": len(rej["rejected"])},
            "unpublished": bool(git), "canUndo": bool(UNDO)}


def snapshot():
    UNDO.append({p.name: (p.read_text(encoding="utf-8") if p.exists() else None) for p in (DATA, CANDS, REJECTED)})
    del UNDO[:-50]


def undo():
    if not UNDO:
        return False
    for name, text in UNDO.pop().items():
        p = ROOT / "data" / name
        if text is None:
            p.unlink(missing_ok=True)
        else:
            p.write_text(text, encoding="utf-8")
    return True


def approve(cand, rec):
    data = read(DATA, {})
    kind = cand["kind"]
    if kind == "festival":
        rec["id"] = rec.get("id") or slug(rec["name"] + "-" + rec["start"][:4])
        for k in ("lat", "lon"):
            rec[k] = float(rec[k])
        data.setdefault("festivals", [])
        data["festivals"] = [f for f in data["festivals"] if f["id"] != rec["id"]] + [rec]
    elif kind == "show":
        rec["artists"] = [a.strip() for a in (rec.get("artists") or []) if a.strip()] if isinstance(rec.get("artists"), list) else [a.strip() for a in str(rec.get("artists", "")).split(",") if a.strip()]
        rec["start"] = rec.get("start") or None
        rec["id"] = rec.get("id") or slug(f"{rec['venue']}-{rec['title'] or ' '.join(rec['artists'])}")
        data["shows"] = [s for s in data["shows"] if s["id"] != rec["id"]] + [rec]
    elif kind == "event":
        nums = [int(e["id"][1:]) for e in data["events"] if re.fullmatch(r"e\d+", e["id"])]
        rec["id"] = rec.get("id") or f"e{max(nums, default=0) + 1:03d}"
        rec["show"] = rec.get("show") or None
        data["events"] = data["events"] + [rec]
    elif kind == "venue":
        rec["lat"], rec["lon"] = float(rec["lat"]), float(rec["lon"])
        data["venues"] = [v for v in data["venues"] if v["id"] != rec["id"]] + [rec]
    else:
        raise ValueError(f"unknown kind {kind}")
    write(DATA, data)


def decide(cid, decision, rec):
    cands = read(CANDS, {"candidates": []})
    cand = next((c for c in cands["candidates"] if c["id"] == cid), None)
    if not cand:
        raise ValueError("candidate not found")
    snapshot()
    rec = rec or cand["record"]
    if decision == "approve":
        approve(cand, dict(rec))
    else:
        rej = read(REJECTED, {"rejected": []})
        rej["rejected"].append({"key": key_of({"kind": cand["kind"], "record": rec if rec.get("name") or rec.get("title") else cand["record"]}),
                                "kind": cand["kind"], "name": rec.get("name") or rec.get("title") or "", "at": dt.date.today().isoformat()})
        write(REJECTED, rej)
    cands["candidates"] = [c for c in cands["candidates"] if c["id"] != cid]
    write(CANDS, cands)


def run(cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def publish():
    log = []
    for title, cmd in (("Check the data", [sys.executable, "tools/validate_data.py"]), ("Rebuild the site pages", [sys.executable, "tools/build_site.py"])):
        code, out = run(cmd)
        log.append(f"== {title}\n{out}")
        if code:
            return False, "\n\n".join(log) + "\n\nStopped. Nothing was published."
    run(["git", "add", "-A"])
    code, out = run(["git", "diff", "--cached", "--quiet"])
    if code == 0:
        return True, "\n\n".join(log) + "\n\nNothing new to publish."
    d = read(DATA, {})
    _, out = run(["git", "commit", "-m", f"Curated additions: {len(d.get('festivals', []))} festivals, {len(d['shows'])} shows, {len(d['events'])} events"])
    log.append("== Commit\n" + out)
    run(["git", "pull", "--rebase", "origin", "main"])
    code, out = run(["git", "push", "origin", "main"])
    log.append("== Push\n" + (out or "done"))
    return code == 0, "\n\n".join(log)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def reply(self, code, body, ctype="application/json"):
        raw = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(raw)

    def host_ok(self):
        return self.headers.get("Host", "").split(":")[0] in ("127.0.0.1", "localhost")

    def do_GET(self):
        if not self.host_ok():
            return self.reply(403, "forbidden", "text/plain")
        if self.path == "/":
            return self.reply(200, PAGE.replace("__TOKEN__", TOKEN), "text/html")
        if self.path == "/api/state" and self.headers.get("X-Curate-Token") == TOKEN:
            with LOCK:
                return self.reply(200, json.dumps(state()))
        self.reply(404, "not found", "text/plain")

    def do_POST(self):
        if not self.host_ok() or self.headers.get("X-Curate-Token") != TOKEN:
            return self.reply(403, json.dumps({"error": "forbidden"}))
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or "{}")
        try:
            with LOCK:
                if self.path == "/api/decide":
                    decide(body["id"], body["decision"], body.get("record"))
                    return self.reply(200, json.dumps(state()))
                if self.path == "/api/undo":
                    undo()
                    return self.reply(200, json.dumps(state()))
                if self.path == "/api/publish":
                    ok, log = publish()
                    return self.reply(200, json.dumps({"ok": ok, "log": log, **state()}))
        except Exception as e:  # report to the page instead of crashing the server
            return self.reply(400, json.dumps({"error": str(e)}))
        self.reply(404, json.dumps({"error": "not found"}))


PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Review candidates · Weekly VERNI</title><meta name="token" content="__TOKEN__">
<style>
:root{--paper:#f1f0f4;--ink:#17151d;--mute:#5c5770;--line:#c9c5d6;--card:#fff;--mark:#5b3cff;--yes:#0d7a52;--no:#b3261e}
@media(prefers-color-scheme:dark){:root{--paper:#0e0d13;--ink:#ebe8f2;--mute:#a29cb5;--line:#3a3646;--card:#15131b;--mark:#a08aff;--yes:#4fd69c;--no:#ff8a80}}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.45 system-ui,-apple-system,sans-serif}
header{display:flex;gap:12px;align-items:center;justify-content:space-between;padding:14px 20px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--paper)}
h1{font-size:1.1rem;margin:0}main{max-width:760px;margin:0 auto;padding:20px}
.card{background:var(--card);border-radius:18px;padding:20px;border:1px solid var(--line)}
.kind{display:inline-block;font-size:.75rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase;background:var(--mark);color:var(--paper);padding:2px 10px;border-radius:99px}
.note{background:rgba(120,100,255,.1);padding:10px 12px;border-radius:10px;margin:12px 0;font-size:.875rem}
label{display:grid;gap:4px;font-size:.8125rem;color:var(--mute);margin-top:10px}input,select{font:inherit;color:var(--ink);background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:10px 12px;width:100%}
.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}a{color:var(--mark)}
.actions{display:flex;gap:10px;margin-top:18px;flex-wrap:wrap}button{font:inherit;font-weight:700;border:0;border-radius:99px;padding:14px 26px;cursor:pointer;color:var(--paper)}
.yes{background:var(--yes)}.no{background:var(--no)}.ghost{background:transparent;color:var(--ink);border:1px solid var(--line)}button:disabled{opacity:.4;cursor:default}
.muted{color:var(--mute);font-size:.8125rem}pre{white-space:pre-wrap;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;font-size:.8125rem}
kbd{border:1px solid var(--line);border-radius:6px;padding:0 6px;font-size:.75rem}
</style></head><body>
<header><h1>Review candidates <span id="left" class="muted"></span></h1><div><button class="ghost" id="undo" style="padding:8px 16px">Undo (Z)</button> <button class="yes" id="publish" style="padding:8px 18px">Publish</button></div></header>
<main><div id="view"></div><pre id="log" hidden></pre><p class="muted" id="foot"></p></main>
<script>
const TOKEN=document.querySelector('meta[name=token]').content; let S=null, skipped=new Set();
const api=async(p,b)=>{const r=await fetch(p,{method:b?'POST':'GET',headers:{'X-Curate-Token':TOKEN,'Content-Type':'application/json'},body:b?JSON.stringify(b):undefined});const j=await r.json();if(!r.ok)throw new Error(j.error||r.status);return j};
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const KINDS=['film','media-art','photography','performance','art-week','other'], TYPES=['gallery','institution','foundation','offspace'], EVT=['opening','finissage','talk','tour','performance'];
const FIELDS={
 festival:[['name','Name'],['kind','Type',KINDS],['city','City','CITIES'],['place','Place'],['start','Start (yyyy-mm-dd)'],['end','End (yyyy-mm-dd)'],['lat','Latitude'],['lon','Longitude'],['url','Official website']],
 show:[['venue','Venue','VENUES'],['artists','Artists (comma separated)'],['title','Title'],['start','Start (empty if unknown)'],['end','End (yyyy-mm-dd)'],['url','Page about the show']],
 event:[['venue','Venue','VENUES'],['type','Type',EVT],['title','Title'],['date','Date (yyyy-mm-dd)'],['time','Time (hh:mm)'],['show','Show id (optional)'],['url','Page']],
 venue:[['id','Id (short, lower case)'],['name','Name'],['type','Type',TYPES],['city','City','CITIES'],['address','Address'],['website','Website'],['lat','Latitude'],['lon','Longitude']]};
function current(){return S.candidates.find(c=>!skipped.has(c.id))||null}
function field([k,l,opts],rec){let v=rec[k]; if(Array.isArray(v))v=v.join(', ');
 if(opts){const list=opts==='CITIES'?S.cities.map(c=>[c,c]):opts==='VENUES'?S.venues.map(x=>[x.id,x.name+' ('+x.city+')']):opts.map(o=>[o,o]);
  return `<label>${l}<select data-k="${k}">${list.map(([a,b])=>`<option value="${esc(a)}"${a===v?' selected':''}>${esc(b)}</option>`).join('')}</select></label>`}
 return `<label>${l}<input data-k="${k}" value="${esc(v)}"></label>`}
function render(){const c=current(), n=S.candidates.length;
 document.getElementById('left').textContent=n?`· ${n} waiting`:'';
 document.getElementById('undo').disabled=!S.canUndo; document.getElementById('publish').disabled=!S.unpublished;
 document.getElementById('foot').textContent=`Live data: ${S.counts.festivals} festivals, ${S.counts.shows} shows, ${S.counts.events} events. ${S.counts.rejected} rejected before.${S.unpublished?' You have changes that are not published yet.':''}`;
 const v=document.getElementById('view');
 if(!c){v.innerHTML=`<div class="card"><h2 style="margin-top:0">${n?'You skipped everything left':'Nothing to review'}</h2><p>${n?'Reload to see the skipped ones again.':'The next refresh will bring new candidates. When you have approved something, press Publish.'}</p></div>`;return}
 const rec=c.record, f=FIELDS[c.kind]||[];
 v.innerHTML=`<div class="card"><span class="kind">${esc(c.kind)}</span> <span class="muted">found ${esc(c.foundAt||'')}</span>
 <h2 style="margin:10px 0 0">${esc(rec.name||rec.title||(rec.artists||[]).join(', '))}</h2>
 ${c.note?`<div class="note">${esc(c.note)}</div>`:''}
 <p class="muted">Source: ${c.source?`<a href="${esc(c.source)}" target="_blank" rel="noopener noreferrer">${esc(c.source)}</a>`:'none'}${rec.url?` · Official: <a href="${esc(rec.url)}" target="_blank" rel="noopener noreferrer">${esc(rec.url)}</a>`:''}</p>
 <div class="row">${f.map(x=>field(x,rec)).join('')}</div>
 <div class="actions"><button class="yes" data-d="approve">Yes, publish this <kbd>Y</kbd></button><button class="no" data-d="reject">No <kbd>N</kbd></button><button class="ghost" data-d="skip">Skip <kbd>S</kbd></button></div></div>`}
function collect(c){const rec={...c.record};document.querySelectorAll('#view [data-k]').forEach(e=>{const k=e.dataset.k;let v=e.value.trim();if(k==='artists')v=v?v.split(',').map(s=>s.trim()).filter(Boolean):[];if(['lat','lon'].includes(k)&&v!=='')v=Number(v);if(['start','show','time'].includes(k)&&v==='')v=null;rec[k]=v});return rec}
async function act(d){const c=current();if(!c)return;if(d==='skip'){skipped.add(c.id);return render()}
 try{S=await api('/api/decide',{id:c.id,decision:d,record:collect(c)});render()}catch(e){alert('Could not save: '+e.message)}}
document.getElementById('view').addEventListener('click',e=>{const b=e.target.closest('[data-d]');if(b)act(b.dataset.d)});
document.getElementById('undo').onclick=async()=>{S=await api('/api/undo',{});skipped.clear();render()};
document.getElementById('publish').onclick=async()=>{const b=document.getElementById('publish'),l=document.getElementById('log');b.disabled=true;b.textContent='Publishing…';l.hidden=false;l.textContent='Working…';
 try{const r=await api('/api/publish',{});l.textContent=r.log;S=r;}catch(e){l.textContent='Failed: '+e.message}b.textContent='Publish';render()};
document.addEventListener('keydown',e=>{if(/input|select|textarea/i.test(e.target.tagName)||e.metaKey||e.ctrlKey)return;const k=e.key.toLowerCase();if(k==='y')act('approve');if(k==='n')act('reject');if(k==='s')act('skip');if(k==='z')document.getElementById('undo').click()});
api('/api/state').then(s=>{S=s;render()}).catch(e=>{document.getElementById('view').innerHTML='<div class="card">Could not load: '+esc(e.message)+'</div>'});
</script></body></html>"""


if __name__ == "__main__":
    port = int(os.environ.get("CURATE_PORT", "8123"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"Review tool running at {url}\nPress Ctrl-C to stop.")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
