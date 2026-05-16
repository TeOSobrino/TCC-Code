#!/usr/bin/env bash
set -euo pipefail

# Cria pod temporário para copiar datasets locais para o PVC do cluster.
kubectl -n pcap-testbed apply -f k8s/utils-dataset-loader.yaml
kubectl -n pcap-testbed wait --for=condition=Ready pod/dataset-loader --timeout=120s

kubectl -n pcap-testbed exec dataset-loader -- mkdir -p /datasets/UNSW-NB15 /datasets/CIC-IDS2017 /datasets/CIC-IDS2018
kubectl -n pcap-testbed cp datasets/UNSW-NB15/. dataset-loader:/datasets/UNSW-NB15/
kubectl -n pcap-testbed cp datasets/CIC-IDS2017/. dataset-loader:/datasets/CIC-IDS2017/
kubectl -n pcap-testbed cp datasets/CIC-IDS2018/. dataset-loader:/datasets/CIC-IDS2018/

kubectl -n pcap-testbed delete pod dataset-loader
