from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os, json, time, uuid, base64, threading, array, random, re
from collections import deque
import requests

# ========= CONFIG =========
LLM_SERVER_URL = os.environ.get("LLM_SERVER_URL", "").strip()  # e.g. https://abc123.tunnel.app
PORT = int(os.environ.get("BBY_PORT", "8420"))
PAINT_W, PAINT_H = 64, 64
MAX_UPLOAD_MB = 8
FADE_TICK_SECONDS = 60          # how often the fade loop runs
AUTOSNAP_IDLE_AFTER = 60        # seconds after last paint to autosnap if a burst was active
BURST_WINDOW = 30               # seconds to count burst
BURST_THRESHOLD_PX = 200        # pixels in window to mark a burst
STATE_SYNC_HZ = 2.0             # pull remote /api/state this many times per second (if available)
# ====== FADE PROBABILITIES (tuned) ======
P_SHORT  = 0.001    # ~0.1%
P_MEDIUM = 0.899    # ~89.9%
P_LONG   = 0.100    # ~10.0%
LIFESPAN_SCALE = 1.0
MIN_FADE_SECONDS = 20 * 60      # 20 min minimum fade span
STROKE_COHERENCE = True
COHERENCE_JITTER = 0.12
REPAINT_REFRESHES_LIFE = True   # repaint with a>0 refreshes lifespan
REPAINT_POLICY = "diff_color_refresh"  # "always" | "never" | "diff_color_refresh"

# ========= APP & STORAGE =========
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_MB * 1024 * 1024
CORS(app)

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
STORE_DIR = os.path.join(BASE_DIR, "storage")
SNAP_DIR  = os.path.join(STORE_DIR, "snapshots")
GALL_DIR  = os.path.join(STORE_DIR, "gallery")
os.makedirs(STORE_DIR, exist_ok=True)
os.makedirs(SNAP_DIR,  exist_ok=True)
os.makedirs(GALL_DIR,  exist_ok=True)

SNAP_IDX  = os.path.join(SNAP_DIR, "index.json")
GALL_IDX  = os.path.join(GALL_DIR, "index.json")
CHAT_FILE = os.path.join(STORE_DIR, "chatHistory.json")
PAINT_STATE_FILE    = os.path.join(STORE_DIR, "paintState.raw")
PAINT_TS_FILE       = os.path.join(STORE_DIR, "paintTimestamps.raw")
PAINT_LIFE_FILE     = os.path.join(STORE_DIR, "paintLifespans.raw")
PAINT_ALPHA0_FILE   = os.path.join(STORE_DIR, "paintAlpha0.raw")
BBYBOOK_LOCAL       = os.path.join(STORE_DIR, "bbybook.json")

# ========= HELPERS =========
def _load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, path)

def _b64_to_bytes(s: str) -> bytes:
    m = re.match(r'^data:image/\w+;base64,(.+)$', s, re.I)
    return base64.b64decode(m.group(1) if m else s)

def _sample_total_seconds():
    u = random.random()
    if u < P_SHORT:
        return random.uniform(2*60, 60*60)          # 2–60 min
    elif u < P_SHORT + P_MEDIUM:
        return random.uniform(4*3600, 144*3600)     # 4–144 h
    else:
        return random.uniform(6*24*3600, 21*24*3600)# 6–21 days

def _split_linger_fade(total_seconds: float):
    linger_frac = random.uniform(0.0, 0.25)
    start = total_seconds * linger_frac
    end = max(start + 1.0, total_seconds)
    if (end - start) < MIN_FADE_SECONDS:
        end = start + MIN_FADE_SECONDS
    return float(start), float(end)

# ========= RUNTIME STATE =========
chat_lock = threading.Lock()
paint_lock = threading.Lock()
events_lock = threading.Lock()
state_lock = threading.Lock()
activity_lock = threading.Lock()

chat_history   = _load_json(CHAT_FILE, [])
snapshot_index = _load_json(SNAP_IDX, [])
gallery_index  = _load_json(GALL_IDX, [])

babyState = {
    "eyes": 5, "mouth": 1,
    "cheeks_on": False, "tears_on": False, "jumping": False,
    "stretch_left": False, "stretch_right": False, "stretch_up": False, "stretch_down": False,
    "squish_left": False, "squish_right": False, "squish_up": False, "squish_down": False,
    "isSpeaking": False, "speechText": "",
    "R": 133, "G": 239, "B": 238,
    "cerebralLoad": 0.0, "dreamIntensity": 0.0, "memoryFlux": 0.0, "learningStability": 0.0,
    "metabolicRate": 0.0,
}

PIX_COUNT = PAINT_W * PAINT_H
RGBA_SIZE = PIX_COUNT * 4
paint_rgba   = bytearray(RGBA_SIZE)
paint_ts     = array.array('L', [0] * PIX_COUNT)
paint_life   = array.array('f', [0.0] * (PIX_COUNT * 2))
paint_alpha0 = array.array('B', [0] * PIX_COUNT)

# load persisted buffers
try:
    if os.path.exists(PAINT_STATE_FILE):
        with open(PAINT_STATE_FILE, "rb") as f: paint_rgba[:] = f.read()
    if os.path.exists(PAINT_TS_FILE):
        with open(PAINT_TS_FILE, "rb") as f: paint_ts.fromfile(f, PIX_COUNT)
    if os.path.exists(PAINT_LIFE_FILE):
        with open(PAINT_LIFE_FILE, "rb") as f: paint_life.fromfile(f, PIX_COUNT*2)
    if os.path.exists(PAINT_ALPHA0_FILE):
        with open(PAINT_ALPHA0_FILE, "rb") as f: paint_alpha0.fromfile(f, PIX_COUNT)
except Exception as e:
    print("[WARN] could not load paint buffers:", e)

# incremental paint events
paint_events = deque(maxlen=2000)  # {id, ts, pixels:[{x,y,r,g,b,a}]}

# activity for autosnapshots
recent_paints = deque()   # (ts, count)
last_paint_ts = 0.0
burst_active = False
burst_start_ts = 0.0
last_autosnap_ts = 0.0
last_autosnap_id = None

# ========= SNAPSHOTS/GALLERY HELPERS =========
def _save_snapshot(label=""):
    snap_id = str(uuid.uuid4())
    ts = int(time.time())
    raw_path   = os.path.join(SNAP_DIR, f"{snap_id}.raw")
    state_path = os.path.join(SNAP_DIR, f"{snap_id}.state.json")
    with paint_lock, state_lock:
        paint_bytes = bytes(paint_rgba)
        state_json  = json.dumps(dict(babyState), ensure_ascii=False).encode("utf-8")
    try:
        with open(raw_path, "wb") as f: f.write(paint_bytes)
        with open(state_path, "wb") as f: f.write(state_json)
    except Exception as e:
        print("[ERROR] snapshot write:", e)
        return None
    meta = {"id": snap_id, "ts": ts, "label": label, "has_png": False}
    snapshot_index.append(meta)
    _save_json(SNAP_IDX, snapshot_index)
    return meta

def _attach_png(snap_id: str, png_bytes: bytes):
    png_path = os.path.join(SNAP_DIR, f"{snap_id}.png")
    try:
        with open(png_path, "wb") as f: f.write(png_bytes)
        for m in snapshot_index:
            if m["id"] == snap_id:
                m["has_png"] = True
                break
        _save_json(SNAP_IDX, snapshot_index)
    except Exception as e:
        print("[ERROR] attach png:", e)

def _add_to_gallery(image_bytes: bytes, author="anon", title="", label="", snap_id=None):
    if not image_bytes:
        raise ValueError("empty image")
    if len(image_bytes) > MAX_UPLOAD_MB*1024*1024:
        raise ValueError("image too large")
    gid = str(uuid.uuid4()); ts = int(time.time())
    fname = f"{ts}_{gid}.png"
    path = os.path.join(GALL_DIR, fname)
    with open(path, "wb") as f: f.write(image_bytes)
    meta = {"id": gid, "ts": ts, "file": fname, "author": author, "title": title or label, "label": label or title}
    if snap_id: meta["snap_id"] = snap_id
    gallery_index.append(meta)
    if len(gallery_index) > 5000: del gallery_index[:-5000]
    _save_json(GALL_IDX, gallery_index)
    return meta

# ========= BACKGROUND LOOPS =========
def _register_paint(n):
    global last_paint_ts, burst_active, burst_start_ts
    now = time.time()
    with activity_lock:
        last_paint_ts = now
        recent_paints.append((now, n))
        cutoff = now - BURST_WINDOW
        while recent_paints and recent_paints[0][0] < cutoff:
            recent_paints.popleft()
        total = sum(k for _, k in recent_paints)
        if not burst_active and total >= BURST_THRESHOLD_PX:
            burst_active = True
            burst_start_ts = now

def pixel_aging_loop():
    print("[PIXEL_AGING] active")
    global burst_active, last_autosnap_ts, last_autosnap_id
    while True:
        changed = []
        try:
            now = int(time.time())
            with paint_lock:
                for i in range(PIX_COUNT):
                    ts = paint_ts[i]
                    if ts == 0: continue
                    age = now - ts
                    a_idx = i*4 + 3
                    cur_a = paint_rgba[a_idx]
                    start_fade = paint_life[i*2]
                    end_fade   = paint_life[i*2+1]
                    if end_fade <= start_fade:
                        continue
                    new_a = cur_a
                    if age > end_fade:
                        if cur_a > 0:
                            new_a = 0
                            paint_ts[i] = 0
                            paint_life[i*2] = 0.0
                            paint_life[i*2+1] = 0.0
                            paint_alpha0[i] = 0
                    elif age > start_fade:
                        frac = (age - start_fade) / (end_fade - start_fade)
                        frac = max(0.0, min(1.0, frac))
                        frac = frac * frac  # ease-out
                        alpha0 = paint_alpha0[i] or cur_a or 255
                        new_a = int(alpha0 * (1.0 - frac))
                    if new_a != cur_a:
                        paint_rgba[a_idx] = max(0, min(255, new_a))
                        x = i % PAINT_W; y = i // PAINT_W
                        off = i*4
                        changed.append({
                            "x": x, "y": y,
                            "r": paint_rgba[off+0], "g": paint_rgba[off+1],
                            "b": paint_rgba[off+2], "a": paint_rgba[off+3],
                        })
                if changed:
                    with open(PAINT_STATE_FILE, "wb") as f: f.write(paint_rgba)
                    with open(PAINT_TS_FILE, "wb") as f: paint_ts.tofile(f)
                    with open(PAINT_LIFE_FILE, "wb") as f: paint_life.tofile(f)
                    with open(PAINT_ALPHA0_FILE, "wb") as f: paint_alpha0.tofile(f)
            if changed:
                ev = {"id": str(uuid.uuid4()), "ts": time.time(), "pixels": changed}
                with events_lock:
                    paint_events.append(ev)
        except Exception as e:
            print("[ERROR] pixel_aging:", e)
        # autosnap check
        try:
            with activity_lock:
                idle = (time.time() - last_paint_ts) if last_paint_ts else 1e9
                do_snap = burst_active and idle >= AUTOSNAP_IDLE_AFTER
            if do_snap:
                meta = _save_snapshot(label="auto-burst")
                if meta:
                    with activity_lock:
                        burst_active = False
                        last_autosnap_ts = time.time()
                        last_autosnap_id = meta["id"]
                    print(f"[AUTOSNAP] {last_autosnap_id}")
        except Exception as e:
            print("[ERROR] autosnap:", e)
        time.sleep(FADE_TICK_SECONDS)

def state_sync_loop():
    if not LLM_SERVER_URL:
        print("[STATE_SYNC] skipped (no LLM_SERVER_URL)")
        return
    print("[STATE_SYNC] active")
    period = 1.0 / max(STATE_SYNC_HZ, 0.1)
    while True:
        try:
            r = requests.get(f"{LLM_SERVER_URL.rstrip('/')}/api/state", timeout=3)
            if r.ok:
                s = r.json()
                with state_lock:
                    babyState.update(s)
        except Exception:
            pass
        time.sleep(period)

threading.Thread(target=pixel_aging_loop, daemon=True).start()
threading.Thread(target=state_sync_loop, daemon=True).start()

# ========= ROUTES =========
@app.get("/api/ping")
def ping():
    return jsonify(ok=True, msg="hello from server")

@app.get("/api/state")
def get_state():
    with state_lock:
        return jsonify(babyState)

@app.post("/api/state")
def set_state():
    data = request.json or {}
    allow = ("R","G","B","eyes","mouth","cheeks_on","tears_on","jumping",
             "stretch_left","stretch_right","stretch_up","stretch_down",
             "squish_left","squish_right","squish_up","squish_down")
    with state_lock:
        for k in allow:
            if k in data:
                v = data[k]
                if k in ("R","G","B","eyes","mouth"): v = int(v)
                babyState[k] = v
    return jsonify(ok=True)

@app.get("/api/chat_history")
def api_chat_history():
    with chat_lock:
        return jsonify(chat_history)

@app.post("/api/say")
def api_say():
    data = request.json or {}
    text = (data.get("text") or "").strip()
    author = (data.get("author") or "anon").strip()
    if not text:
        return jsonify(status="error", reply="no text :("), 400
    user_msg = {"id": str(uuid.uuid4()), "author": author, "text": text, "timestamp": time.time()}
    with chat_lock:
        chat_history.append(user_msg)
        if len(chat_history) > 500: chat_history[:] = chat_history[-500:]
        _save_json(CHAT_FILE, chat_history)
    # proxy to LLM
    reply = "... (no response)"
    try:
        if LLM_SERVER_URL:
            r = requests.post(f"{LLM_SERVER_URL.rstrip('/')}/api/say",
                              json={"text": text, "author": author}, timeout=180)
            if r.ok:
                reply = r.json().get("reply", reply)
    except Exception as e:
        print("[ERR] say proxy:", e)
    # refresh state from LLM (to pick up colour)
    try:
        if LLM_SERVER_URL:
            r = requests.get(f"{LLM_SERVER_URL.rstrip('/')}/api/state", timeout=5)
            if r.ok:
                with state_lock:
                    babyState.update(r.json())
    except Exception:
        pass
    bot_msg = {"id": str(uuid.uuid4()), "author": "babyLLM", "text": reply, "timestamp": time.time(),
               "colour": {"r": babyState.get("R",133), "g": babyState.get("G",239), "b": babyState.get("B",238)}}
    with chat_lock:
        chat_history.append(bot_msg)
        if len(chat_history) > 500: chat_history[:] = chat_history[-500:]
        _save_json(CHAT_FILE, chat_history)
    return jsonify(status="ok", reply=reply)

@app.get("/api/bbybook")
def api_bbybook():
    # Prefer remote (freshest), else local file if present
    if LLM_SERVER_URL:
        try:
            r = requests.get(f"{LLM_SERVER_URL.rstrip('/')}/api/bbybook", timeout=5)
            if r.ok:
                return jsonify(r.json())
        except Exception:
            pass
    if os.path.exists(BBYBOOK_LOCAL):
        try:
            return jsonify(_load_json(BBYBOOK_LOCAL, {}))
        except Exception as e:
            print("[WARN] local bbybook:", e)
    return jsonify({})

# ---- Pixels ----
@app.get("/api/get_paint_canvas")
def api_get_paint_canvas():
    with paint_lock:
        b64 = base64.b64encode(paint_rgba).decode("utf-8")
    return jsonify(paintOverlayData_b64=b64, w=PAINT_W, h=PAINT_H)

@app.post("/api/paint_pixel")
def api_paint_pixel():
    data = request.json or {}
    pixels = data.get("pixels")
    if not isinstance(pixels, list) or not pixels:
        return jsonify(status="error", message="bad payload"), 400
    now = int(time.time())
    ev_pixels = []
    with paint_lock:
        stroke_base = _sample_total_seconds() if STROKE_COHERENCE else None
        for p in pixels:
            try:
                x,y = int(p["x"]), int(p["y"])
                r,g,b,a = int(p["r"]),int(p["g"]),int(p["b"]),int(p["a"])
            except Exception:
                continue
            if not (0 <= x < PAINT_W and 0 <= y < PAINT_H): continue
            idx = y*PAINT_W + x
            off = idx*4
            old_r, old_g, old_b = paint_rgba[off], paint_rgba[off+1], paint_rgba[off+2]
            same_rgb = (old_r == r and old_g == g and old_b == b)
            # choose refresh
            if REPAINT_REFRESHES_LIFE and a > 0:
                refresh = True
            else:
                if REPAINT_POLICY == "always":
                    refresh = True
                elif REPAINT_POLICY == "never":
                    refresh = (paint_ts[idx] == 0)
                else:  # diff_color_refresh
                    refresh = (paint_ts[idx] == 0) or (not same_rgb)
            # write pixel
            paint_rgba[off:off+4] = bytes((r,g,b,a))
            if a > 0:
                if refresh:
                    paint_ts[idx] = now
                    total = stroke_base * random.uniform(1-COHERENCE_JITTER, 1+COHERENCE_JITTER) if stroke_base else _sample_total_seconds()
                    total *= LIFESPAN_SCALE
                    start_fade, end_fade = _split_linger_fade(total)
                    paint_life[idx*2] = float(start_fade)
                    paint_life[idx*2+1] = float(end_fade)
                    paint_alpha0[idx] = a
            else:
                paint_ts[idx] = 0
                paint_life[idx*2] = 0.0
                paint_life[idx*2+1] = 0.0
                paint_alpha0[idx] = 0
            ev_pixels.append({"x":x,"y":y,"r":r,"g":g,"b":b,"a":a})
        # persist
        with open(PAINT_STATE_FILE, "wb") as f: f.write(paint_rgba)
        with open(PAINT_TS_FILE, "wb") as f: paint_ts.tofile(f)
        with open(PAINT_LIFE_FILE, "wb") as f: paint_life.tofile(f)
        with open(PAINT_ALPHA0_FILE, "wb") as f: paint_alpha0.tofile(f)
    if ev_pixels:
        _register_paint(len(ev_pixels))
        ev = {"id": str(uuid.uuid4()), "ts": time.time(), "pixels": ev_pixels}
        with events_lock:
            paint_events.append(ev)
    return jsonify(status="ok", changed=len(ev_pixels))

@app.get("/api/paint_events")
def api_paint_events():
    since = request.args.get("since", "")
    with events_lock:
        events = list(paint_events)
    if not events:
        return jsonify([])
    if not since:
        return jsonify([{"id": events[-1]["id"], "pixels": []}])
    out = []
    for ev in reversed(events):
        if ev["id"] == since: break
        out.append(ev)
    out.reverse()
    return jsonify(out)

# ---- Snapshots ----
@app.post("/api/snapshot")
def api_snapshot():
    data = request.json or {}
    label = (data.get("label") or "").strip()
    meta = _save_snapshot(label)
    if not meta:
        return jsonify(status="error", message="failed"), 500
    b64 = data.get("composite_png_b64")
    if b64:
        try:
            _attach_png(meta["id"], _b64_to_bytes(b64))
            meta["has_png"] = True
        except Exception as e:
            print("[WARN] attach composite:", e)
    return jsonify(status="ok", snapshot=meta)

@app.post("/api/snapshot_attach_png/<sid>")
def api_snapshot_attach_png(sid):
    data = request.json or {}
    b64 = data.get("composite_png_b64")
    if not b64:
        return jsonify(error="missing composite_png_b64"), 400
    try:
        _attach_png(sid, _b64_to_bytes(b64))
        return jsonify(status="ok")
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.get("/api/snapshots")
def api_snapshots():
    base = request.host_url.rstrip("/")
    out = []
    for m in snapshot_index:
        it = dict(m)
        if it.get("has_png"):
            it["png_url"] = f"{base}/api/snapshots/{it['id']}.png"
        out.append(it)
    return jsonify(out)

@app.get("/api/snapshots/<sid>.png")
def api_snapshot_png(sid):
    path = os.path.join(SNAP_DIR, f"{sid}.png")
    if not os.path.exists(path): return ("not found", 404)
    return send_from_directory(SNAP_DIR, f"{sid}.png", mimetype="image/png")

@app.get("/api/snapshot/<sid>")
def api_snapshot_raw(sid):
    raw_path = os.path.join(SNAP_DIR, f"{sid}.raw")
    state_path = os.path.join(SNAP_DIR, f"{sid}.state.json")
    if not (os.path.exists(raw_path) and os.path.exists(state_path)):
        return jsonify(error="not found"), 404
    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)
    return jsonify(state=state)

# ---- Gallery ----
@app.post("/api/gallery/save")
def api_gallery_save():
    try:
        body = request.get_data(cache=False)
        if body:
            img = body
            author = request.headers.get("x-author") or "anon"
            title  = request.headers.get("x-title")  or ""
            label  = request.headers.get("x-label")  or ""
            snap_id= request.headers.get("x-snap-id") or None
        else:
            j = request.get_json(silent=True) or {}
            b64 = j.get("png_b64", "").strip()
            if not b64: return jsonify(ok=False, error="missing png_b64"), 400
            img = _b64_to_bytes(b64)
            author = str(j.get("author") or "anon")
            title  = str(j.get("title")  or "")
            label  = str(j.get("label")  or "")
            snap_id= str(j.get("snap_id")) if j.get("snap_id") else None
        meta = _add_to_gallery(img, author=author, title=title, label=label, snap_id=snap_id)
        base = request.host_url.rstrip("/")
        return jsonify(ok=True, id=meta["id"], url=f"{base}/api/gallery/file/{meta['file']}", title=meta.get("title",""))
    except ValueError as e:
        return jsonify(ok=False, error=str(e)), 413
    except Exception as e:
        return jsonify(ok=False, error=f"{type(e).__name__}: {e}"), 500

@app.get("/api/gallery")
def api_gallery_list():
    base = request.host_url.rstrip("/")
    out = []
    for m in reversed(gallery_index[-200:]):
        it = dict(m)
        it["url"] = f"{base}/api/gallery/file/{m['file']}"
        out.append(it)
    return jsonify(out)

@app.post("/api/gallery/update_meta")
def api_gallery_update_meta():
    data = request.get_json(force=True) or {}
    gid = (data.get("id") or "").strip()
    if not gid: return jsonify(ok=False, error="missing id"), 400
    new_title = (data.get("title") or "").strip()
    new_label = (data.get("label") or "").strip()
    found = False
    for m in gallery_index:
        if m.get("id") == gid:
            if new_title:
                m["title"] = new_title
                if not new_label:
                    m["label"] = m.get("label") or new_title
            if new_label:
                m["label"] = new_label
            found = True
            break
    if not found: return jsonify(ok=False, error="not found"), 404
    _save_json(GALL_IDX, gallery_index)
    return jsonify(ok=True)

@app.get("/api/gallery/file/<fname>")
def api_gallery_file(fname):
    if not fname.endswith(".png"): return ("forbidden", 403)
    path = os.path.join(GALL_DIR, fname)
    if not os.path.exists(path): return ("not found", 404)
    return send_from_directory(GALL_DIR, fname, mimetype="image/png")

# ---- Activity ----
@app.get("/api/activity")
def api_activity():
    now = time.time()
    with activity_lock:
        total = sum(n for t,n in recent_paints if t >= now - BURST_WINDOW)
        idle  = (now - last_paint_ts) if last_paint_ts else 1e9
        return jsonify(pixels_last_window=total, window_seconds=BURST_WINDOW,
                       idle_seconds=idle, burst_active=burst_active,
                       burst_started=burst_start_ts if burst_active else None,
                       last_autosnap_id=last_autosnap_id, last_autosnap_ts=last_autosnap_ts)

# ========= RUN =========
if __name__ == "__main__":
    print(f"=== VPS bbyServer on 127.0.0.1:{PORT} (LLM at {LLM_SERVER_URL or 'none'}) ===")
    app.run(host="127.0.0.1", port=PORT)

