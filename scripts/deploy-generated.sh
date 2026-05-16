#!/usr/bin/env bash
set -euo pipefail

kubectl apply -f k8s/generated/00-namespace.yaml
kubectl apply -f k8s/generated/01-pvc.yaml
kubectl apply -f k8s/generated/02-central.yaml
kubectl apply -f k8s/generated/03-edges.yaml
kubectl apply -f k8s/generated/04-iot-devices.yaml
kubectl apply -f k8s/generated/05-replayers.yaml

echo "[OK] Topologia gerada implantada"
kubectl -n pcap-testbed get pods -o wide
