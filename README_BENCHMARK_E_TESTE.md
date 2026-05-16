# Benchmark prático após gerar a topologia

Nesta versão, `MODEL_BACKEND=dummy` significa **nenhum modelo executado**.

Ele serve como baseline de **0 overhead de inferência**:

```text
captura tcpdump → estatísticas mínimas → envio de evento
```

O dummy não calcula score, não classifica e não carrega TensorFlow.

## 1. Gerar uma topologia

Exemplo com 6 dispositivos IoT e 2 nós de borda:

```bash
./scripts/generate-topology.sh 6 2 dummy true
```

Verifique a árvore:

```bash
cat k8s/generated/TOPOLOGY.md
```

## 2. Implantar

```bash
./scripts/build-images.sh
./scripts/deploy-generated.sh
```

Aguardar os pods:

```bash
kubectl -n pcap-testbed get pods -w
```

## 3. Verificar comunicação básica

Servidor central:

```bash
kubectl -n pcap-testbed logs deployment/central-server -f
```

Edges:

```bash
kubectl -n pcap-testbed logs -l role=edge -f
```

IoTs:

```bash
kubectl -n pcap-testbed logs -l role=iot -f
```

## 4. Copiar PCAPs para o PVC

Estrutura local esperada:

```text
datasets/
├── UNSW-NB15/sample.pcap
├── CIC-IDS2017/sample.pcap
└── CIC-IDS2018/sample.pcap
```

Copiar:

```bash
./scripts/copy-pcaps-to-pvc.sh
```

## 5. Executar replay manual de PCAP

UNSW-NB15:

```bash
kubectl -n pcap-testbed create job --from=cronjob/pcap-replay-unsw-nb15 replay-unsw-test
```

CIC-IDS2017:

```bash
kubectl -n pcap-testbed create job --from=cronjob/pcap-replay-cic-ids2017 replay-cic2017-test
```

CIC-IDS2018:

```bash
kubectl -n pcap-testbed create job --from=cronjob/pcap-replay-cic-ids2018 replay-cic2018-test
```

Ver logs do job:

```bash
kubectl -n pcap-testbed logs job/replay-unsw-test -f
```

## 6. Coletar eventos do servidor central

Use port-forward:

```bash
kubectl -n pcap-testbed port-forward svc/central-server 8080:8080
```

Em outro terminal:

```bash
curl http://localhost:8080/events | python3 -m json.tool
```

## 7. Rodar benchmark automático

```bash
./scripts/run-benchmark.sh UNSW-NB15 dummy true
```

O script:
1. limpa jobs antigos;
2. dispara replay;
3. aguarda execução;
4. coleta eventos;
5. salva resultado em `benchmark-results/`.

## 8. Comparar dummy vs modelo real

Baseline 0 overhead:

```bash
./scripts/generate-topology.sh 6 2 dummy true
./scripts/deploy-generated.sh
./scripts/run-benchmark.sh UNSW-NB15 dummy true
```

Modelo real FL-NIDS:

```bash
./scripts/copy-model-to-pvc.sh /caminho/para/fl_model.h5
./scripts/generate-topology.sh 6 2 flnids true
./scripts/deploy-generated.sh
./scripts/run-benchmark.sh UNSW-NB15 flnids true
```

Depois compare os campos:

```json
"metrics": {
  "capture_ms": ...,
  "feature_ms": ...,
  "inference_ms": ...,
  "cycle_ms": ...
}
```

No modo dummy, `inference_ms` deve ficar próximo de zero, pois não há inferência real.

## 9. Limpeza

```bash
./scripts/delete-generated.sh
kubectl delete namespace pcap-testbed
```
