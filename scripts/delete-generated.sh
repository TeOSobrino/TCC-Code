#!/usr/bin/env bash
set -euo pipefail

kubectl delete -f k8s/generated/05-replayers.yaml --ignore-not-found
kubectl delete -f k8s/generated/04-iot-devices.yaml --ignore-not-found
kubectl delete -f k8s/generated/03-edges.yaml --ignore-not-found
kubectl delete -f k8s/generated/02-central.yaml --ignore-not-found
