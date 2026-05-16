#!/usr/bin/env bash
set -euo pipefail

MODEL_FILE="${1:-fl_model.h5}"

if [ ! -f "$MODEL_FILE" ]; then
  echo "Uso: $0 caminho/para/fl_model.h5"
  exit 1
fi

kubectl -n pcap-testbed apply -f k8s/utils-model-loader.yaml
kubectl -n pcap-testbed wait --for=condition=Ready pod/model-loader --timeout=120s

kubectl -n pcap-testbed cp "$MODEL_FILE" model-loader:/models/fl_model.h5

kubectl -n pcap-testbed delete pod model-loader
echo "[OK] Modelo copiado para /models/fl_model.h5"
