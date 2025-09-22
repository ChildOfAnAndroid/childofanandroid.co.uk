from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import os, json, time, uuid, base64, threading, array, random, re, io
import hashlib
from collections import deque
import requests
from urllib.parse import unquote
try:
    from PIL import Image
except Exception:
    Image = None

# ========= CONFIG =========
LLM_SERVER_URL = os.environ.get("LLM_SERVER_URL", "").strip()
if not LLM_SERVER_URL:
    print("\n[FATAL] LLM_SERVER_URL environment variable is not set!")
    print("This server cannot function without knowing where the brain server is.")
    print("Please set it and restart.\n")
PORT = int(os.environ.get("BBY_PORT", "8420"))
PAINT_W, PAINT_H = 64, 64
MAX_UPLOAD_MB = 8
FADE_TICK_SECONDS = 60          # how often the fade loop runs
AUTOSNAP_IDLE_AFTER = 60        # seconds after last paint to autosnap if a burst was active
BURST_WINDOW = 30               # seconds to count burst
BURST_THRESHOLD_PX = 200        # pixels in window to mark a burst
STATE_SYNC_HZ = 10.0            # pull remote /api/state this many times per second (if available)
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

# Guest handling for non‑opted‑in external users
# 'pooled'  -> all guests per platform share a single UID (e.g., 'discord:guest')
# 'hashed'  -> per-user anonymous shadow UID (not persisted)
# 'reject'  -> block non-opt-in entirely
GUEST_POLICY = os.environ.get("BBY_GUEST_POLICY", "pooled").strip().lower()

# ========= APP & STORAGE =========
app = Flask(__name__)
# Trust reverse proxy headers so Flask knows it's behind HTTPS
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
app.config['PREFERRED_URL_SCHEME'] = 'https'
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

# --- USER DATABASE ---
USERS_FILE = os.path.join(STORE_DIR, "users.json")

def _load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_users(users: dict):
    tmp = USERS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)
    os.replace(tmp, USERS_FILE)

def _reload_users_from_disk():
    """Refresh in-memory `users` from the on-disk users.json.
    Useful when aliases or edits were made externally (e.g., via a script)."""
    global users
    try:
        on_disk = _load_users()
        if isinstance(on_disk, dict):
            users.clear()
            users.update(on_disk)
    except Exception as e:
        print("[WARN] could not reload users:", e)

def _slug(s: str) -> str:
    try:
        return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    except Exception:
        return ""

users = _load_users()

def _mk_uid(platform: str, user_id: str, fallback_author: str = "anon") -> str:
    """Create a stable UID like 'web:abc123' or 'discord:123456'.
    Uses provided args only; does not read request data.
    """
    platform = (platform or "web").strip().lower()
    uid_part = str(user_id or "").strip() or str(fallback_author or "anon").strip()
    return f"{platform}:{uid_part}"

def _upsert_user(platform: str, user_id: str, handle: str = None, display_name: str = None, colour: dict | None = None):
    uid = _mk_uid(platform, user_id, display_name or handle)
    rec = users.get(uid, {
        "platform": platform,
        "user_id": user_id,
        "handle": None,
        "display_name": None,
        "nicknames": [],
        "colour": None,
        "last_seen": 0,
        "message_count": 0,
        "loyalty": 1,
        "inventory": {},
        "favourites": []
    })
    if handle: rec["handle"] = handle
    if display_name: rec["display_name"] = display_name
    if isinstance(colour, dict): rec["colour"] = colour
    rec["last_seen"] = time.time()
    rec["message_count"] = float(rec.get("message_count", 0)) + 1.0
    users[uid] = rec
    _save_users(users)
    return uid

# --- Consent + guest helpers ---
def _safe_hash(s: str) -> str:
    try:
        return hashlib.sha256((s or '').encode('utf-8')).hexdigest()[:12]
    except Exception:
        return 'anon'

def _is_opted_in(platform: str, user_id: str) -> bool:
    uid = _mk_uid(platform, user_id, None)
    rec = users.get(uid)
    if not rec:
        return False
    consents = rec.get('consents', {})
    return bool(consents.get(platform))

def _guest_uid(platform: str, user_id: str) -> str:
    if GUEST_POLICY == 'pooled':
        return f"{platform}:guest"
    elif GUEST_POLICY == 'hashed':
        return f"{platform}:guest:{_safe_hash(user_id)}"
    else:
        return 'reject'

def _looks_like_command(text: str) -> bool:
    return bool(re.match(r"^\s*[!/]", text or ""))
PAINT_STATE_FILE    = os.path.join(STORE_DIR, "paintState.raw")
PAINT_TS_FILE       = os.path.join(STORE_DIR, "paintTimestamps.raw")
PAINT_LIFE_FILE     = os.path.join(STORE_DIR, "paintLifespans.raw")
PAINT_ALPHA0_FILE   = os.path.join(STORE_DIR, "paintAlpha0.raw")
BBYBOOK_LOCAL       = os.path.join(STORE_DIR, "bbybook.json")
GALLERY_ADMIN_TOKEN = os.environ.get("GALLERY_ADMIN_TOKEN", "").strip()

# Prefer proxy-provided scheme/host when building absolute URLs
from flask import request as _request_for_base

def _get_base_url():
    proto = _request_for_base.headers.get('X-Forwarded-Proto', _request_for_base.scheme)
    host  = _request_for_base.headers.get('X-Forwarded-Host', _request_for_base.host)
    return f"{proto}://{host}".rstrip("/")

# === Brain (local Mac) proxy helpers ===
def _brain_url(path: str) -> str:
    base = (LLM_SERVER_URL or '').rstrip('/')
    path = '/' + path.lstrip('/')
    return base + path

def _brain_post(path: str, payload: dict, timeout=15):
    try:
        url = _brain_url(path)
        r = requests.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": f"brain post failed: {e}"}

def _brain_get(path: str, timeout=10):
    try:
        url = _brain_url(path)
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": f"brain get failed: {e}"}

# ========= HELPERS =========
def _load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _save_json(path, data):
    """
    Atomically save JSON and, if it's one of our critical indexes, write a timestamped backup.
    """
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)

    # Write a timestamped backup for critical files
    try:
        critical = {GALL_IDX, SNAP_IDX, USERS_FILE, CHAT_FILE}
        if path in critical:
            backup_dir = os.path.join(os.path.dirname(path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
            base = os.path.basename(path)
            backup_path = os.path.join(backup_dir, f"{base}.{stamp}.json")
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("[WARN] could not write backup for", path, "->", e)

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
state_lock = threading.Lock()
paint_lock = threading.Lock()
events_lock = threading.Lock()
activity_lock = threading.Lock()
chat_lock = threading.Lock()

snapshot_index = _load_json(SNAP_IDX, [])
gallery_index  = _load_json(GALL_IDX, [])
chat_history   = _load_json(CHAT_FILE, [])

# This is a *cached* copy of the state from the brain server.
babyState = { "eyes": 5, "mouth": 1, "isSpeaking": False, "R": 133, "G": 239, "B": 238 }

PIX_COUNT = PAINT_W * PAINT_H
paint_rgba   = bytearray(PIX_COUNT * 4)
paint_ts     = array.array('L', [0] * PIX_COUNT)
paint_life   = array.array('f', [0.0] * (PIX_COUNT * 2))
paint_alpha0 = array.array('B', [0] * PIX_COUNT)

try:  # Load persisted paint buffers
    if os.path.exists(PAINT_STATE_FILE):
        with open(PAINT_STATE_FILE, "rb") as f:
            paint_rgba[:] = f.read(PIX_COUNT * 4)
    if os.path.exists(PAINT_TS_FILE):
        with open(PAINT_TS_FILE, "rb") as f:
            arr = array.array('L')
            arr.fromfile(f, PIX_COUNT)
            paint_ts = arr
    if os.path.exists(PAINT_LIFE_FILE):
        with open(PAINT_LIFE_FILE, "rb") as f:
            arr = array.array('f')
            arr.fromfile(f, PIX_COUNT * 2)
            paint_life = arr
    if os.path.exists(PAINT_ALPHA0_FILE):
        with open(PAINT_ALPHA0_FILE, "rb") as f:
            arr = array.array('B')
            arr.fromfile(f, PIX_COUNT)
            paint_alpha0 = arr
except Exception as e:
    print("[WARN] could not load paint buffers:", e)

paint_events = deque(maxlen=2000)
recent_paints = deque()
last_paint_ts = 0.0
burst_active = False
burst_start_ts = 0.0
last_autosnap_ts = 0.0
last_autosnap_id = None

# ========= SNAPSHOTS/GALLERY HELPERS =========
def _save_snapshot(label=""):
    snap_id, ts = str(uuid.uuid4()), int(time.time())
    raw_path = os.path.join(SNAP_DIR, f"{snap_id}.raw")
    state_path = os.path.join(SNAP_DIR, f"{snap_id}.state.json")
    print(f"[_save_snapshot] Attempting to save snapshot {snap_id}...")
    with paint_lock, state_lock:
        paint_bytes = bytes(paint_rgba); state_json  = json.dumps(dict(babyState), ensure_ascii=False).encode("utf-8")
    try:
        with open(raw_path, "wb") as f: f.write(paint_bytes)
        with open(state_path, "wb") as f: f.write(state_json)
    except Exception as e:
        print(f"[_save_snapshot][FATAL] FAILED TO WRITE SNAPSHOT FILES for {snap_id}: {e}")
        print("[_save_snapshot] This might be a file permissions issue on the server!")
        return None
    meta = {"id": snap_id, "ts": ts, "label": label, "has_png": False}; snapshot_index.append(meta); _save_json(SNAP_IDX, snapshot_index)
    print(f"[_save_snapshot] Successfully saved snapshot {snap_id}.")
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


def _crop_transparent_to_square(image_bytes: bytes) -> bytes:
    """
    Crops transparent padding, then places the result onto a new, perfectly
    square canvas, ensuring the final image has a 1:1 aspect ratio.
    """
    if Image is None:
        return image_bytes
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img = img.convert("RGBA")

            # 1. Get the tightest bounding box of the content
            bbox = img.getbbox()
            if not bbox:
                # Image is fully transparent, return a 1x1 transparent pixel
                return Image.new("RGBA", (1, 1), (0,0,0,0)).tobytes()

            # 2. Crop to the tightest rectangle first
            cropped = img.crop(bbox)
            width, height = cropped.size

            # 3. Determine the size of the new square canvas
            max_dim = max(width, height)

            # 4. Create a new transparent square canvas
            square_canvas = Image.new("RGBA", (max_dim, max_dim), (0, 0, 0, 0))

            # 5. Calculate position to paste the cropped image to center it
            paste_x = (max_dim - width) // 2
            paste_y = (max_dim - height) // 2

            # 6. Paste the cropped image onto the square canvas
            square_canvas.paste(cropped, (paste_x, paste_y))

            # 7. Save and return the final square image bytes
            out = io.BytesIO()
            square_canvas.save(out, format="PNG")
            return out.getvalue()
    except Exception as e:
        print(f"[_crop_transparent_to_square] failed: {e}")
    # Fallback to original bytes on error
    return image_bytes

def _add_to_gallery(image_bytes: bytes, author="anon", title="", label="", snap_id=None):
    if not image_bytes:
        raise ValueError("empty image")
    if len(image_bytes) > MAX_UPLOAD_MB*1024*1024:
        raise ValueError("image too large")
    image_bytes = _crop_transparent_to_square(image_bytes)
    gid = str(uuid.uuid4()); ts = int(time.time())
    fname = f"{ts}_{gid}.png"
    path = os.path.join(GALL_DIR, fname)
    with open(path, "wb") as f: f.write(image_bytes)

    # --- NEW STAMP LOGIC ---
    stamp_fname = None
    MAX_STAMP_DIM = 96 # Align with bbyWorld.vue
    try:
        if Image is None: raise Exception("Pillow not installed")

        with Image.open(io.BytesIO(image_bytes)) as img:
            img = img.convert("RGBA")
            stamp_img = None

            if snap_id:
                # Snapshots are from a 64x64 source, so resize to that
                if img.width != 64 or img.height != 64:
                    stamp_img = img.resize((64, 64), Image.Resampling.NEAREST)
            elif img.width > MAX_STAMP_DIM or img.height > MAX_STAMP_DIM:
                # For test grid images, thumbnail preserves aspect ratio
                stamp_img = img.copy()
                stamp_img.thumbnail((MAX_STAMP_DIM, MAX_STAMP_DIM), Image.Resampling.NEAREST)

            if stamp_img:
                stamp_fname = f"{ts}_{gid}.stamp.png"
                stamp_path = os.path.join(GALL_DIR, stamp_fname)
                out_buffer = io.BytesIO()
                stamp_img.save(out_buffer, format="PNG")
                with open(stamp_path, "wb") as f:
                    f.write(out_buffer.getvalue())

    except Exception as e:
        print(f"[WARN] Failed to create stamp for {gid}: {e}")
        stamp_fname = None
    # --- END NEW STAMP LOGIC ---

    meta = {"id": gid, "ts": ts, "file": fname, "author": author, "title": title or label, "label": label or title}
    if snap_id: meta["snap_id"] = snap_id
    if stamp_fname: meta["stamp_file"] = stamp_fname
    gallery_index.append(meta)
    if len(gallery_index) > 5000: del gallery_index[:-5000]
    _save_json(GALL_IDX, gallery_index)
    return meta

# ---- Gallery index import / merge (recovery) ----
def _validate_gallery_item(it: dict) -> dict | None:
    """
    Validate and normalize a gallery index item. Returns cleaned dict or None.
    """
    if not isinstance(it, dict):
        return None
    file = it.get("file") or ""
    if not isinstance(file, str) or not file.endswith(".png"):
        return None
    out = {
        "id": str(it.get("id") or uuid.uuid4()),
        "ts": int(it.get("ts") or time.time()),
        "author": str(it.get("author") or "anon"),
        "title": str(it.get("title") or it.get("label") or ""),
        "label": str(it.get("label") or it.get("title") or ""),
        "file": file
    }
    # carry optional fields if present
    if isinstance(it.get("snap_id"), str):
        out["snap_id"] = it["snap_id"]
    if isinstance(it.get("stamp_file"), str):
        out["stamp_file"] = it["stamp_file"]
    return out

@app.post("/api/gallery/import_index")
def api_gallery_import_index():
    """
    Replace or merge the gallery index from a posted JSON payload.
    Body:
    {
        "index": [ ...items... ],
        "mode": "replace" | "merge"   (default: replace)
    }
    Matching is done by 'file' (preferred) then by 'id' if present.
    """
    try:
        payload = request.get_json(silent=True) or {}
        items = payload.get("index")
        mode = (payload.get("mode") or "replace").strip().lower()
        if not isinstance(items, list) or not items:
            return jsonify(error="missing or invalid 'index' array"), 400

        cleaned = []
        for it in items:
            v = _validate_gallery_item(it)
            if v:
                cleaned.append(v)

        if not cleaned:
            return jsonify(error="no valid items to import"), 400

        imported = 0
        updated = 0

        global gallery_index
        if mode == "replace":
            gallery_index = cleaned
            imported = len(cleaned)
        else:
            # merge mode: keep existing, update/insert by 'file' fallback 'id'
            existing_by_file = {it["file"]: i for i, it in enumerate(gallery_index) if isinstance(it, dict) and it.get("file")}
            existing_by_id   = {it.get("id"): i for i, it in enumerate(gallery_index) if isinstance(it, dict) and it.get("id")}
            for it in cleaned:
                idx = existing_by_file.get(it["file"])
                if idx is None and it.get("id"):
                    idx = existing_by_id.get(it["id"])
                if idx is None:
                    gallery_index.append(it)
                    imported += 1
                else:
                    gallery_index[idx] = it
                    updated += 1

        # keep only the newest 5000 like saver does
        if len(gallery_index) > 5000:
            gallery_index = gallery_index[-5000:]

        _save_json(GALL_IDX, gallery_index)
        return jsonify(ok=True, mode=mode, imported=imported, updated=updated, total=len(gallery_index))
    except Exception as e:
        return jsonify(error=f"import failed: {e}"), 500

def _claim_alias_if_exists(platform: str, display_name: str, handle: str, real_uid: str):
    """If an alias record like '{platform}:alias:{slug(name)}' exists and is unclaimed,
    merge its fields into the real user and mark it claimed_by=real_uid.
    Tries both display_name and handle as candidates."""
    _reload_users_from_disk()

    def _merge_from_alias(alias_uid: str) -> bool:
        rec = users.get(alias_uid)
        if not rec or rec.get("claimed_by"):
            return False

        real = users.get(real_uid, {
            "platform": platform,
            "user_id": real_uid.split(":",1)[1],
            "handle": None,
            "display_name": None,
            "nicknames": [],
            "colour": None,
            "last_seen": 0,
            "message_count": 0.0,
            "loyalty": 1,
            "inventory": {},
            "favourites": []
        })

        if not real.get("display_name") and rec.get("display_name"):
            real["display_name"] = rec.get("display_name")
        if not real.get("handle") and rec.get("handle"):
            real["handle"] = rec.get("handle")
        if rec.get("colour") and not real.get("colour"):
            real["colour"] = rec.get("colour")

        try:
            real["message_count"] = float(real.get("message_count", 0)) + float(rec.get("message_count", 0) or 0)
        except Exception:
            pass
        real["loyalty"]   = max(real.get("loyalty", 1), rec.get("loyalty", 1))
        real["last_seen"] = max(real.get("last_seen", 0), rec.get("last_seen", 0))

        inv_real  = real.setdefault("inventory", {})
        inv_alias = rec.get("inventory") or {}
        if isinstance(inv_alias, dict):
            for k, v in inv_alias.items():
                try:
                    inv_real[k] = int(inv_real.get(k, 0)) + int(v)
                except Exception:
                    continue

        fav   = set(real.get("favourites", []) or []) | set(rec.get("favourites", []) or [])
        nicks = set(real.get("nicknames",  []) or []) | set(rec.get("nicknames",  []) or [])
        real["favourites"] = list(fav)
        real["nicknames"]  = list(nicks)

        if isinstance(rec.get("consents"), dict):
            c = real.setdefault("consents", {})
            for k, v in rec["consents"].items():
                c.setdefault(k, v)

        users[real_uid] = real
        rec["claimed_by"] = real_uid
        users[alias_uid] = rec
        _save_users(users)
        return True

    tried = set()
    for candidate in (display_name, handle):
        if not candidate:
            continue
        alias_uid = f"{platform}:alias:{_slug(candidate)}"
        if alias_uid in tried:
            continue
        tried.add(alias_uid)
        if _merge_from_alias(alias_uid):
            break

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
        print("[STATE_SYNC] FATAL: loop cannot run as LLM_SERVER_URL is not set.")
        return
    print(f"[STATE_SYNC] active, polling {LLM_SERVER_URL} at {STATE_SYNC_HZ}Hz")
    base_period = 1.0 / max(STATE_SYNC_HZ, 0.1)
    period = base_period
    failures = 0
    while True:
        try:
            r = requests.get(f"{LLM_SERVER_URL.rstrip('/')}/api/state", timeout=2)
            if r.ok:
                with state_lock:
                    babyState.update(r.json())
                failures = 0
                period = base_period
            elif random.randint(0, 50) == 0:
                print(f"[STATE_SYNC][WARN] Failed to sync state, brain returned status: {r.status_code}")
        except requests.exceptions.RequestException:
            failures += 1
            if failures == 1 or failures % 5 == 0:
                print(f"[STATE_SYNC][WARN] Could not connect to brain server at {LLM_SERVER_URL}.")
            period = min(period * 2, 60)
        time.sleep(period)

threading.Thread(target=pixel_aging_loop, daemon=True).start()
threading.Thread(target=state_sync_loop, daemon=True).start()

# ========= ROUTES =========
@app.post("/api/speak")
def api_speak():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    author = (data.get("author") or data.get("display_name") or "anon").strip()
    if not text: return jsonify(error="missing text"), 400
    brain_resp = _brain_post("/api/say", {"text": text, "author": author})
    return jsonify(brain_resp), 200

@app.get("/api/ping")
def ping(): return jsonify(ok=True, msg="hello from server")

@app.get("/api/state")
def get_state():
    with state_lock: return jsonify(babyState)

# --- Proxy POST for /api/state ---

@app.post("/api/state")
def api_set_state():
    data = request.get_json(silent=True) or {}
    _reload_users_from_disk()
    if not isinstance(data, dict):
        return jsonify(error="no json body"), 400
    if not LLM_SERVER_URL:
        return jsonify(error="brain not configured"), 503
    try:
        r = requests.post(f"{LLM_SERVER_URL.rstrip('/')}/api/state", json=data, timeout=5)
        return (r.text, r.status_code, {"Content-Type": r.headers.get("Content-Type","application/json")})
    except requests.exceptions.RequestException as e:
        return jsonify(error=f"brain unreachable: {e}"), 504

# --- Legacy aliases (frontend might call /state) ---
@app.get("/state")
def legacy_get_state():
    return get_state()

@app.post("/state")
def legacy_post_state():
    return api_set_state()

@app.get("/api/chat_history")
def api_chat_history():
    try:
        with chat_lock:
            public_events = [
                {
                    "id": e.get("id"),
                    "author": e.get("author") or "anon",
                    "text": e.get("text") or "",
                    "colour": e.get("colour") or {"r":133,"g":239,"b":208},
                }
                for e in chat_history
                if e.get("visible_on_web") is True
            ]
        if len(public_events) > 200: public_events = public_events[-200:]
        return jsonify(public_events)
    except Exception as e: return jsonify(error=f"chat history failed: {e}"), 500

# --- Legacy alias (frontend might call /chat_history) ---
@app.get("/chat_history")
def legacy_chat_history():
    return api_chat_history()

# --- Consent route ---
@app.post('/api/consent')
def api_consent():
    data = request.get_json(silent=True) or {}
    platform     = (data.get("platform") or "web").strip().lower()
    visible_on_web = (platform == "web")
    user_id = (data.get('user_id') or '').strip()
    handle = (data.get('handle') or '').strip() or None
    display_name = (data.get('display_name') or '').strip() or None
    colour = data.get('colour') or None
    consent_flag = bool(data.get('consent', True))
    if not user_id:
        return jsonify(error='missing user_id'), 400
    uid = _mk_uid(platform, user_id, display_name or handle)
    if consent_flag:
        # ensure record exists and mark consent
        _upsert_user(platform=platform, user_id=user_id, handle=handle, display_name=display_name, colour=colour)
        users[uid].setdefault('consents', {})[platform] = int(time.time())
        try: _claim_alias_if_exists(platform, display_name or (handle or ""), handle or (display_name or ""), uid)
        except Exception as e: print('[WARN] alias-claim in consent failed:', e)
        _save_users(users)
    else:
        rec = users.get(uid)
        if rec:
            rec.setdefault('consents', {}).pop(platform, None)
            users[uid] = rec
            _save_users(users)
    return jsonify(ok=True, uid=uid, consents=users.get(uid, {}).get('consents', {}))

@app.post("/api/say")
def api_say():
    """Proxies the chat message to the brain server and records history."""
    data = request.json or {}
    _reload_users_from_disk()
    text = (data.get("text") or "").strip()
    author = (data.get("author") or "anon").strip()
    platform     = (data.get("platform") or "web").strip().lower()
    visible_on_web = (platform == "web")
    user_id = (data.get("user_id") or author or "anon").strip()
    handle = (data.get("handle") or author).strip()
    display_name = (data.get("display_name") or author).strip()
    colour = data.get("colour") or None

    # Normalise colour
    if isinstance(colour, dict):
        try:
            r = int(colour.get("r", 133)); g = int(colour.get("g", 239)); b = int(colour.get("b", 238))
            colour = {"r": r, "g": g, "b": b}
        except Exception:
            colour = None
    else:
        colour = None

    if not text:
        return jsonify(status="error", reply="no text :("), 400

    # Decide if we persist this user/message
    is_command = bool(data.get("is_command")) or _looks_like_command(text)
    persist_user = True
    if platform in ('discord', 'twitch') and not _is_opted_in(platform, user_id):
        persist_user = False

    if persist_user:
        uid = _upsert_user(platform=platform, user_id=user_id, handle=handle, display_name=display_name, colour=colour)
        _claim_alias_if_exists(platform, display_name, handle, uid)
    else:
        uid = _guest_uid(platform, user_id)
        if uid == 'reject': return jsonify(status='error', reply='you are chatting as a guest; opt in to play!'), 403

    # Only append to chat history if persisted user OR the message is a command
    if persist_user or is_command:
        user_msg = {
            "id": str(uuid.uuid4()),
            "uid": uid,
            "author": display_name,
            "text": text,
            "timestamp": time.time(),
            "visible_on_web": visible_on_web,
        }
        if colour is not None: user_msg["colour"] = colour
        with chat_lock:
            chat_history.append(user_msg)
            if len(chat_history) > 500:
                chat_history[:] = chat_history[-500:]
            _save_json(CHAT_FILE, chat_history)

    reply = "... (brain is offline)"
    status_code = 503
    if LLM_SERVER_URL:
        try:
            r = requests.post(
                f"{LLM_SERVER_URL.rstrip('/')}/api/say",
                json={"text": text, "author": author},
                timeout=185 # Slightly longer than brain timeout
            )
            status_code = r.status_code
            if r.ok:
                reply = r.json().get("reply", "... (brain gave empty reply)")
            else:
                reply = f"... (brain error: {r.status_code})"
        except requests.exceptions.RequestException as e:
            print("[ERROR] /api/say proxy failed:", e)
            reply = "... (could not reach brain)"
            status_code = 504 # Gateway timeout

    # The brain server now handles its own color, so we just get the latest state
    with state_lock:
        bot_color = {"r": babyState.get("R",133), "g": babyState.get("G",239), "b": babyState.get("B",238)}
    
    bot_msg = {
        "id": str(uuid.uuid4()),
        "author": "babyLLM",
        "text": reply,
        "timestamp": time.time(),
        "colour": bot_color,
        "visible_on_web": (platform == "web"),  # Baby’s own replies only appear if the original was web
    }
    with chat_lock:
        chat_history.append(bot_msg)
        if len(chat_history) > 500: chat_history[:] = chat_history[-500:]
        _save_json(CHAT_FILE, chat_history)

    speak = data.get("speak")
    if speak is None:
        speak = (platform == "web")  # default: web messages speak
    if speak:
        brain_resp = _brain_post("/api/say", {"text": text, "author": display_name})
        msg["brain_reply"] = brain_resp.get("reply") if isinstance(brain_resp, dict) else None
    
    return jsonify(
        status=("ok" if status_code == 200 else "error"),
        reply=reply,
        uid=uid,
        guest=(not persist_user and platform in ('discord','twitch'))
    ), status_code


# --- Optional: Read-only endpoint to fetch a user record by uid ---
@app.get('/api/users/<path:uid>')
def api_get_user(uid: str):
    _reload_users_from_disk()
    rec = users.get(uid)
    if not rec: return jsonify(error='not found'), 404
    return jsonify(rec)

@app.get("/api/bbybook")
def api_bbybook():
    """Gets the bbybook from the brain server with a local fallback.

    If the brain server is reachable we return its data and update the cached
    copy on disk.  Otherwise we fall back to the last saved copy if it exists.
    """
    # Try the brain server first if a URL is configured
    if LLM_SERVER_URL:
        try:
            r = requests.get(f"{LLM_SERVER_URL.rstrip('/')}/api/bbybook", timeout=5)
            if r.ok:
                data = r.json()
                # Save a copy so we can serve it later if the brain is offline
                try:
                    with open(BBYBOOK_LOCAL, "w", encoding="utf-8") as f:
                        json.dump(data, f)
                except Exception:
                    pass  # Caching errors shouldn't prevent serving the data
                return jsonify(data)
        except requests.exceptions.RequestException:
            pass  # Fall back to local copy below

    # If we couldn't reach the brain, try the cached local copy
    if os.path.exists(BBYBOOK_LOCAL):
        try:
            with open(BBYBOOK_LOCAL, "r", encoding="utf-8") as f:
                return jsonify(json.load(f))
        except Exception as e:
            return jsonify(error=f"Could not read local bbybook: {e}"), 500

    # No brain data and no local cache – return appropriate error
    if LLM_SERVER_URL:
        return jsonify(error="Could not reach brain server"), 504
    return jsonify(error="Brain server URL not configured"), 503

# ---- Pixels ----
@app.get("/api/get_paint_canvas")
def api_get_paint_canvas():
    with paint_lock:
        b64 = base64.b64encode(paint_rgba).decode("utf-8")
    return jsonify(paintOverlayData_b64=b64, w=PAINT_W, h=PAINT_H)

# --- Legacy alias (frontend might call /get_paint_canvas) ---
@app.get("/get_paint_canvas")
def legacy_get_paint_canvas():
    return api_get_paint_canvas()

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

# --- Legacy alias (frontend might call /paint_events) ---
@app.get("/paint_events")
def legacy_paint_events():
    return api_paint_events()

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
    base = _get_base_url()
    if meta.get("has_png"):
        meta["png_url"] = f"{base}/api/snapshots/{meta['id']}.png"
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
    base = _get_base_url()
    out = []
    # Return newest-first so clients naturally pick the most recent snapshot
    for m in reversed(snapshot_index):
        it = dict(m)
        # provide a stable 'timestamp' alias as well as 'ts'
        if 'timestamp' not in it:
            it['timestamp'] = it.get('ts')
        if it.get("has_png"):
            it["png_url"] = f"{base}/api/snapshots/{it['id']}.png"
        out.append(it)
    return jsonify(out)

# Serve the single most recent snapshot (preferably one with a PNG)
@app.get("/api/snapshots/latest.json")
def api_snapshots_latest():
    base = _get_base_url()
    # prefer the newest item that has a png; otherwise fall back to newest overall
    latest = None
    for m in reversed(snapshot_index):
        if m.get('has_png'):
            latest = m
            break
    if latest is None:
        latest = snapshot_index[-1] if snapshot_index else None
    if not latest:
        return jsonify({}), 200
    it = dict(latest)
    if 'timestamp' not in it:
        it['timestamp'] = it.get('ts')
    if it.get('has_png'):
        it['png_url'] = f"{base}/api/snapshots/{it['id']}.png"
    return jsonify(it)

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
@app.get("/api/gallery/index_count")
def api_gallery_index_count():
    try:
        return jsonify(count=len(gallery_index))
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.post("/api/gallery/save")
def api_gallery_save():
    try:
        body = request.get_data(cache=False)
        if body:
            img = body
            # Headers are ASCII only, so values may be percent-encoded to allow
            # emoji or other unicode characters. Decode them if present.
            author = unquote(request.headers.get("x-author") or "anon")
            title  = unquote(request.headers.get("x-title")  or "")
            label  = unquote(request.headers.get("x-label")  or "")
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
        base = _get_base_url()
        return jsonify(ok=True, id=meta["id"], url=f"{base}/api/gallery/file/{meta['file']}", title=meta.get("title",""))
    except ValueError as e:
        return jsonify(ok=False, error=str(e)), 413
    except Exception as e:
        return jsonify(ok=False, error=f"{type(e).__name__}: {e}"), 500

@app.get("/api/gallery")
def api_gallery_list():
    base = _get_base_url()
    out = []
    for m in reversed(gallery_index[-200:]):
        it = dict(m)
        it["url"] = f"{base}/api/gallery/file/{m['file']}"
        # Provide a stable 'timestamp' alias alongside legacy 'ts'
        if 'timestamp' not in it:
            it['timestamp'] = it.get('ts')
        # Compatibility: some external clients may look for a 'stamp' field
        # intending a timestamp; provide it as an alias to avoid misusing
        # unrelated 'stamp' concepts elsewhere (e.g., thumbnail stamps).
        if 'stamp' not in it:
            it['stamp'] = it.get('ts')
        if m.get("stamp_file"):
            it["stamp_url"] = f"{base}/api/gallery/file/{m['stamp_file']}"
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

# --- Delete a gallery image by id or filename (protected) ---
@app.delete("/api/gallery/<img_id>")
def delete_gallery_image(img_id):
    # auth: require token if configured
    provided = request.headers.get('X-Admin-Token') or request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    if not GALLERY_ADMIN_TOKEN or not provided or provided != GALLERY_ADMIN_TOKEN:
        return jsonify({"status": "error", "message": "forbidden"}), 403

    try:
        # Find the metadata record first, whether by ID or filename
        target_meta = next((m for m in gallery_index if m.get('id') == img_id or m.get('file') == img_id), None)
        if not target_meta:
            return jsonify({"status": "error", "message": "not found"}), 404

        deleted = {}
        target_id = target_meta.get("id")
        
        # Delete main image file
        main_file = target_meta.get('file')
        if main_file:
            path = os.path.join(GALL_DIR, main_file)
            if os.path.isfile(path):
                os.remove(path)
                deleted["image"] = True
        
        # Delete stamp file if it exists
        stamp_file = target_meta.get('stamp_file')
        if stamp_file:
            path = os.path.join(GALL_DIR, stamp_file)
            if os.path.isfile(path):
                os.remove(path)
                deleted["stamp"] = True

        # Remove from index by its ID
        before = len(gallery_index)
        gallery_index[:] = [m for m in gallery_index if m.get('id') != target_id]
        if len(gallery_index) != before:
            deleted["index"] = True
            _save_json(GALL_IDX, gallery_index)

        if not deleted:
            return jsonify({"status": "error", "message": "index entry found but no files to delete"}), 404

        return jsonify({"status": "ok", "deleted": deleted, "id": target_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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
    print(f"=== bby_public_server on 127.0.0.1:{PORT} (Brain at {LLM_SERVER_URL or 'NOT SET!'}) ===")
    app.run(host="0.0.0.0", port=PORT)
