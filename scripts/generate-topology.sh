#!/usr/bin/env bash
set -euo pipefail

IOT_DEVICES="${1:-12}"
EDGE_NODES="${2:-3}"
MODEL_BACKEND="${3:-dummy}"
MODEL_ENABLED="${4:-true}"

python3 -m pip install -q -r topology/requirements.txt

python3 topology/generate_topology.py \
  --config topology/topology.yaml \
  --out k8s/generated \
  --iot-devices "$IOT_DEVICES" \
  --edge-nodes "$EDGE_NODES" \
  --model-backend "$MODEL_BACKEND" \
  --model-enabled "$MODEL_ENABLED"
