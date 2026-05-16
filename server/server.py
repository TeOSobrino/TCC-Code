from flask import Flask, request, jsonify
from collections import deque
import time
import json

app = Flask(__name__)
EVENTS = deque(maxlen=1000)


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "events": len(EVENTS)}


@app.route("/event", methods=["POST"])
def event():
    payload = request.get_json(force=True)
    payload["received_at"] = int(time.time())
    EVENTS.append(payload)

    print("[server] evento recebido:", json.dumps(payload), flush=True)
    return jsonify({"ok": True})


@app.route("/events", methods=["GET"])
def events():
    return jsonify(list(EVENTS))


@app.route("/aggregate", methods=["POST"])
def aggregate():
    # Dummy para futura agregação federada.
    # Aqui entraria FedAvg, IFCEA, SSFL, FLiForest etc.
    payload = request.get_json(force=True, silent=True) or {}
    print("[server] aggregate dummy:", json.dumps(payload), flush=True)

    return jsonify({
        "ok": True,
        "global_model_version": int(time.time()),
        "message": "dummy aggregation executed"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
