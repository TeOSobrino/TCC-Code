#!/usr/bin/env bash
set -euo pipefail

DATASET="${DATASET:-UNSW-NB15}"
PCAP_FILE="${PCAP_FILE:-/datasets/${DATASET}/sample.pcap}"
INTERFACE="${REPLAY_INTERFACE:-eth0}"
LOOP="${LOOP:-1}"
PPS="${PPS:-0}"

echo "[replayer] dataset=${DATASET}"
echo "[replayer] pcap=${PCAP_FILE}"
echo "[replayer] interface=${INTERFACE}"
echo "[replayer] loop=${LOOP}"
echo "[replayer] pps=${PPS}"

if [ ! -f "$PCAP_FILE" ]; then
  echo "[replayer] ERRO: PCAP não encontrado: $PCAP_FILE"
  echo "[replayer] Monte os arquivos no PVC em /datasets/<DATASET>/sample.pcap"
  exit 1
fi

if [ "$PPS" = "0" ]; then
  # --topspeed pode ser trocado por --multiplier 1.0 para tentar preservar timing.
  tcpreplay --intf1="$INTERFACE" --loop="$LOOP" "$PCAP_FILE"
else
  tcpreplay --intf1="$INTERFACE" --loop="$LOOP" --pps="$PPS" "$PCAP_FILE"
fi

echo "[replayer] finalizado"
