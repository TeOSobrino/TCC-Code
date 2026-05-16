# Topologia parametrizável em árvore

Esta versão permite gerar uma arquitetura lógica com:

- `N` dispositivos IoT;
- `M` nós de borda;
- 1 servidor central;
- comunicação lógica em árvore.

```text
central-server
├── edge-0
│   ├── iot-0
│   ├── iot-3
│   └── ...
├── edge-1
│   ├── iot-1
│   ├── iot-4
│   └── ...
└── edge-2
    ├── iot-2
    ├── iot-5
    └── ...
```

## Gerar topologia

12 IoTs, 3 edges, modelo dummy ligado:

```bash
./scripts/generate-topology.sh 12 3 dummy true
```

20 IoTs, 4 edges, FL-NIDS ligado:

```bash
./scripts/generate-topology.sh 20 4 flnids true
```

20 IoTs, 4 edges, modelo desligado:

```bash
./scripts/generate-topology.sh 20 4 flnids false
```

## Implantar

```bash
./scripts/build-images.sh
./scripts/deploy-generated.sh
```

## Ver árvore gerada

```bash
cat k8s/generated/TOPOLOGY.md
```

## Funcionamento

Cada `iot-X` executa o agente IDS, captura tráfego com `tcpdump`, extrai features e envia eventos ao seu pai:

```text
iot-X → edge-Y → central-server
```

Cada `edge-Y` funciona como agregador regional dummy. Ele recebe eventos dos dispositivos filhos e encaminha ao servidor central.

## Diferença entre IoT e Edge

Os manifests gerados configuram recursos diferentes:

| Tipo | Capacidade |
|---|---|
| IoT | Menor CPU/RAM |
| Edge | Maior CPU/RAM |
| Central | Maior CPU/RAM |

## Observação sobre rede

Kubernetes normalmente usa uma rede flat entre pods. A árvore aqui é uma **topologia lógica de comunicação**, não uma árvore física L2/L3.

Para uma árvore de rede estrita em nível de enlace/rede, seria necessário usar CNI avançado, Multus, Linux bridges, namespaces de rede manuais ou Mininet.


## Benchmark 0 overhead

Nesta versão, `MODEL_BACKEND=dummy` não executa nenhum modelo.
Ele é usado como baseline de 0 overhead de inferência.

```bash
./scripts/generate-topology.sh 12 3 dummy true
./scripts/deploy-generated.sh
./scripts/run-benchmark.sh UNSW-NB15 dummy true
```

Para resumir resultados:

```bash
python3 scripts/summarize-benchmark.py benchmark-results/<arquivo>.json
```
