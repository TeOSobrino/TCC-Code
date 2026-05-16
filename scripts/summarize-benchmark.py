#!/usr/bin/env python3
import json
import sys
from statistics import mean, median

if len(sys.argv) < 2:
    print("Uso: python3 scripts/summarize-benchmark.py benchmark-results/arquivo.json")
    sys.exit(1)

path = sys.argv[1]
events = json.load(open(path, "r", encoding="utf-8"))

rows = []
for ev in events:
    metrics = ev.get("metrics", {})
    pred = ev.get("prediction", {})
    rows.append({
        "node": ev.get("node"),
        "model": pred.get("model"),
        "label": pred.get("label"),
        "capture_ms": metrics.get("capture_ms"),
        "feature_ms": metrics.get("feature_ms"),
        "inference_ms": metrics.get("inference_ms"),
        "cycle_ms": metrics.get("cycle_ms"),
        "bytes": ev.get("features", {}).get("bytes"),
    })

def nums(key):
    return [r[key] for r in rows if isinstance(r.get(key), (int, float))]

print(f"Arquivo: {path}")
print(f"Eventos: {len(rows)}")
if rows:
    print(f"Modelos: {sorted(set(str(r['model']) for r in rows))}")
    print(f"Labels: {sorted(set(str(r['label']) for r in rows))}")

for key in ["capture_ms", "feature_ms", "inference_ms", "cycle_ms", "bytes"]:
    values = nums(key)
    if values:
        print(f"{key}: mean={mean(values):.2f} median={median(values):.2f} min={min(values)} max={max(values)}")
