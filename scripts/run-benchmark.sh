#!/usr/bin/env bash
set -euo pipefail

DATASET="${1:-UNSW-NB15}"
MODEL_BACKEND="${2:-dummy}"
MODEL_ENABLED="${3:-true}"
NAMESPACE="${NAMESPACE:-pcap-testbed}"

mkdir -p benchmark-results

case "$DATASET" in
  UNSW-NB15)
    CRONJOB="pcap-replay-unsw-nb15"
    ;;
  CIC-IDS2017)
    CRONJOB="pcap-replay-cic-ids2017"
    ;;
  CIC-IDS2018)
    CRONJOB="pcap-replay-cic-ids2018"
    ;;
  *)
    echo "Dataset inválido: $DATASET"
    echo "Use: UNSW-NB15, CIC-IDS2017 ou CIC-IDS2018"
    exit 1
    ;;
esac

STAMP="$(date +%Y%m%d-%H%M%S)"
JOB="bench-${DATASET,,}-${STAMP}"
JOB="${JOB//_/-}"

echo "[INFO] Configurando modelo: backend=$MODEL_BACKEND enabled=$MODEL_ENABLED"
kubectl -n "$NAMESPACE" set env deployment -l role=iot MODEL_BACKEND="$MODEL_BACKEND" MODEL_ENABLED="$MODEL_ENABLED" || true

echo "[INFO] Aguardando rollout dos IoTs..."
kubectl -n "$NAMESPACE" rollout status deployment -l role=iot --timeout=180s || true

echo "[INFO] Disparando replay: $CRONJOB -> $JOB"
kubectl -n "$NAMESPACE" create job --from=cronjob/"$CRONJOB" "$JOB"

echo "[INFO] Aguardando job concluir..."
kubectl -n "$NAMESPACE" wait --for=condition=complete job/"$JOB" --timeout=300s || {
  echo "[WARN] Job não concluiu dentro do timeout. Logs:"
  kubectl -n "$NAMESPACE" logs job/"$JOB" || true
}

echo "[INFO] Logs do replay:"
kubectl -n "$NAMESPACE" logs job/"$JOB" || true

echo "[INFO] Coletando eventos do servidor central..."
kubectl -n "$NAMESPACE" port-forward svc/central-server 18080:8080 >/tmp/pcap-testbed-portforward.log 2>&1 &
PF_PID="$!"
sleep 3

OUT="benchmark-results/${DATASET}-${MODEL_BACKEND}-${MODEL_ENABLED}-${STAMP}.json"
curl -s http://localhost:18080/events > "$OUT" || true

kill "$PF_PID" >/dev/null 2>&1 || true

echo "[OK] Resultado salvo em $OUT"
echo "[INFO] Para inspecionar:"
echo "python3 -m json.tool $OUT | less"
