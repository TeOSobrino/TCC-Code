#!/usr/bin/env bash
set -euo pipefail

if command -v k3s >/dev/null 2>&1; then
  echo "[OK] k3s já instalado"
else
  echo "[INFO] Instalando k3s..."
  curl -sfL https://get.k3s.io | sh -
fi

mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown "$USER:$USER" ~/.kube/config

kubectl get nodes
