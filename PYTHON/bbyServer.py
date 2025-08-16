from flask import Flask, jsonify, request
from flask_cors import CORS
import os, json, time, uuid

app = Flask(__name__)
CORS(app)

# ====== PATHS (override with env if different) ======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REQUEST_FILE_PATH = os.environ.get("REQUEST_FILE_PATH", os.path.join(BASE_DIR, "bby_request.json"))
RESPONSE_DIR      = os.environ.get("RESPONSE_DIR",      os.path.join(BASE_DIR, "bby_responses"))
STATE_FILE_PATH   = os.environ.get("STATE_FILE_PATH",   os.path.join(BASE_DIR, "babyState.json"))
BBYBOOK_PATH      = os.environ.get("BBYBOOK_PATH",      os.path.expanduser("~/Dropbox/00_Icharis/02_LAB/01_babyLLM/SHKAIRA/soul/bbybook.json"))
os.makedirs(RESPONSE_DIR, exist_ok=True)

TIMEOUT_SECONDS = int(os.environ.get("BRAIN_TIMEOUT", "180"))

@app.get("/api/ping")
def ping():
    return jsonify(ok=True, msg="hello from mac brain")

@app.get("/api/state")
def get_state():
    try:
        if os.path.exists(STATE_FILE_PATH):
            with open(STATE_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return jsonify(data)
    except Exception as e:
        return jsonify(error=f"state read: {e}"), 500
    # default
    return jsonify({"R":133,"G":239,"B":238,"eyes":5,"mouth":1,"isSpeaking":False})

@app.get("/api/bbybook")
def get_bbybook():
    try:
        if os.path.exists(BBYBOOK_PATH):
            with open(BBYBOOK_PATH, "r", encoding="utf-8") as f:
                return jsonify(json.load(f))
    except Exception as e:
        return jsonify(error=f"bbybook read: {e}"), 500
    return jsonify({})

@app.post("/api/say")
def say():
    data = request.json or {}
    text = (data.get("text") or "").strip()
    author = (data.get("author") or "anon").strip()
    if not text:
        return jsonify(status="error", reply="no text :("), 400

    req_id = str(uuid.uuid4())
    req_payload = {"id": req_id, "text": text, "author": author}
    try:
        with open(REQUEST_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(req_payload, f)
    except Exception as e:
        return jsonify(status="error", reply=f"write request failed: {e}"), 500

    # Wait for response file from your local LLM process
    resp_path = os.path.join(RESPONSE_DIR, f"{req_id}.json")
    start = time.time()
    reply = "... (no response)"
    while time.time() - start < TIMEOUT_SECONDS:
        if os.path.exists(resp_path):
            try:
                with open(resp_path, "r", encoding="utf-8") as f:
                    reply = (json.load(f) or {}).get("reply", reply)
            except Exception as e:
                reply = f"... (read error: {e})"
            try:
                os.remove(resp_path)
            except Exception:
                pass
            break
        time.sleep(0.1)

    # mark speaking in babyState.json for local animation
    try:
        if os.path.exists(STATE_FILE_PATH):
            with open(STATE_FILE_PATH, "r", encoding="utf-8") as f:
                st = json.load(f)
        else:
            st = {}
        st["speechText"] = reply
        st["isSpeaking"] = True
        with open(STATE_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(st, f)
    except Exception:
        pass

    return jsonify(status="ok", reply=reply)

if __name__ == "__main__":
    print("=== brain_api (Mac) on http://127.0.0.1:420 ===")
    app.run(host="127.0.0.1", port=4420)
