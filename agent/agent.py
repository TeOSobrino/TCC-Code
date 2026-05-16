import os
import time
import json
import socket
import subprocess
from pathlib import Path
import requests

MODEL_ENABLED = os.getenv("MODEL_ENABLED", "true").lower() == "true"
MODEL_BACKEND = os.getenv("MODEL_BACKEND", "dummy").lower()
SERVER_URL = os.getenv("SERVER_URL", "http://fl-server:8080")
INTERFACE = os.getenv("CAPTURE_INTERFACE", "eth0")
CAPTURE_DIR = Path(os.getenv("CAPTURE_DIR", "/captures"))
CAPTURE_SECONDS = int(os.getenv("CAPTURE_SECONDS", "20"))
NODE_NAME = os.getenv("DEVICE_ID", os.getenv("HOSTNAME", socket.gethostname()))

CAPTURE_DIR.mkdir(parents=True, exist_ok=True)

_real_model = None


def now_ms():
    return int(time.time() * 1000)


def get_real_model():
    global _real_model
    if _real_model is None:
        from real_model import FLNIDSModel
        _real_model = FLNIDSModel()
    return _real_model


def capture_pcap() -> Path:
    ts = int(time.time())
    out = CAPTURE_DIR / f"{NODE_NAME}-{ts}.pcap"

    cmd = [
        "tcpdump",
        "-i", INTERFACE,
        "-w", str(out),
        "-G", str(CAPTURE_SECONDS),
        "-W", "1",
        "-nn"
    ]

    print(f"[agent] capturando trafego: {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=False)
    return out


def extract_basic_capture_stats(pcap_path: Path) -> dict:
    # Estatísticas mínimas para benchmark.
    # Não é extração de features do modelo; apenas mede artefatos de captura.
    size = pcap_path.stat().st_size if pcap_path.exists() else 0
    return {
        "pcap": pcap_path.name,
        "bytes": size,
        "packets_estimate": max(1, size // 128),
        "timestamp": int(time.time())
    }


def no_model_predict(features: dict) -> dict:
    # Benchmark "0 overhead" de inferência:
    # não calcula score, não classifica, não executa modelo.
    return {
        "model": "none",
        "enabled": False,
        "anomaly_score": None,
        "label": "not_evaluated",
        "benchmark_mode": "zero_inference_overhead"
    }


def predict(features: dict) -> dict:
    if not MODEL_ENABLED:
        return no_model_predict(features)

    if MODEL_BACKEND == "dummy":
        # Dummy agora é deliberadamente um no-op para baseline de overhead.
        return no_model_predict(features)

    if MODEL_BACKEND == "flnids":
        return get_real_model().predict(features)

    raise ValueError(f"MODEL_BACKEND inválido: {MODEL_BACKEND}")


def send_event(features: dict, prediction: dict, metrics: dict):
    payload = {
        "node": NODE_NAME,
        "features": features,
        "prediction": prediction,
        "metrics": metrics,
        "model_enabled": MODEL_ENABLED,
        "model_backend": MODEL_BACKEND
    }

    try:
        r = requests.post(f"{SERVER_URL}/event", json=payload, timeout=5)
        print(f"[agent] evento enviado: status={r.status_code} payload={json.dumps(payload)}", flush=True)
    except Exception as exc:
        print(f"[agent] erro ao enviar evento: {exc}", flush=True)


def main():
    print(
        f"[agent] iniciado node={NODE_NAME} "
        f"model_enabled={MODEL_ENABLED} model_backend={MODEL_BACKEND}",
        flush=True
    )

    while True:
        cycle_start = now_ms()

        capture_start = now_ms()
        pcap = capture_pcap()
        capture_end = now_ms()

        feature_start = now_ms()
        features = extract_basic_capture_stats(pcap)
        feature_end = now_ms()

        inference_start = now_ms()
        prediction = predict(features)
        inference_end = now_ms()

        metrics = {
            "capture_ms": capture_end - capture_start,
            "feature_ms": feature_end - feature_start,
            "inference_ms": inference_end - inference_start,
            "cycle_ms": now_ms() - cycle_start
        }

        send_event(features, prediction, metrics)
        time.sleep(2)


if __name__ == "__main__":
    main()
