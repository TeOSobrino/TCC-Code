#!/usr/bin/env bash
set -euo pipefail

kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/02-pvc.yaml
kubectl apply -f k8s/03-server.yaml
kubectl apply -f k8s/04-agent.yaml
kubectl apply -f k8s/05-replayers.yaml

echo "[OK] Deploy concluído"
kubectl -n pcap-testbed get pods
