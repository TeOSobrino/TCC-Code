import os
import time
import json
import requests
from flask import Flask, request, jsonify
from collections import deque

app = Flask(__name__)

EDGE_ID = os.getenv("EDGE_ID", "edge-unknown")
PARENT_SERVER_URL = os.getenv("PARENT_SERVER_URL", "http://central-server:8080")
CHILDREN = [x for x in os.getenv("CHILDREN", "").split(",") if x]

EVENTS = deque(maxlen=1000)


@app.route("/health", methods=["GET"])
def health():
    return {
        "status": "ok",
        "edge_id": EDGE_ID,
        "children": CHILDREN,
        "events": len(EVENTS)
    }


@app.route("/event", methods=["POST"])
def event():
    payload = request.get_json(force=True)
    payload["edge_id"] = EDGE_ID
    payload["edge_received_at"] = int(time.time())
    EVENTS.append(payload)

    print("[edge] evento recebido:", json.dumps(payload), flush=True)

    try:
        r = requests.post(f"{PARENT_SERVER_URL}/event", json=payload, timeout=5)
        forwarded = r.status_code
    except Exception as exc:
        print("[edge] erro ao encaminhar para central:", exc, flush=True)
        forwarded = None

    return jsonify({"ok": True, "forwarded_status": forwarded})


@app.route("/aggregate", methods=["POST"])
def aggregate():
    payload = request.get_json(force=True, silent=True) or {}
    payload["edge_id"] = EDGE_ID
    payload["children"] = CHILDREN

    try:
        r = requests.post(f"{PARENT_SERVER_URL}/aggregate", json=payload, timeout=5)
        status = r.status_code
    except Exception as exc:
        print("[edge] erro no aggregate central:", exc, flush=True)
        status = None

    return jsonify({
        "ok": True,
        "edge_id": EDGE_ID,
        "children": CHILDREN,
        "forwarded_status": status
    })


@app.route("/events", methods=["GET"])
def events():
    return jsonify(list(EVENTS))


if __name__ == "__main__":
    print(f"[edge] iniciado {EDGE_ID} filhos={CHILDREN} parent={PARENT_SERVER_URL}", flush=True)
    app.run(host="0.0.0.0", port=8081)
