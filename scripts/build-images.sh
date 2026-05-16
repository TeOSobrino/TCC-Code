#!/usr/bin/env bash
set -euo pipefail

docker build -t local/pcap-replayer:0.1 ./replayer
docker build -t local/ids-agent:0.1 ./agent
docker build -t local/fl-server:0.1 ./server
docker build -t local/edge-node:0.1 ./edge

docker save local/pcap-replayer:0.1 | sudo k3s ctr images import -
docker save local/ids-agent:0.1 | sudo k3s ctr images import -
docker save local/fl-server:0.1 | sudo k3s ctr images import -
docker save local/edge-node:0.1 | sudo k3s ctr images import -
