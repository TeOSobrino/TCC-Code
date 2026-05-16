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


Para resumir resultados:

```bash
python3 scripts/summarize-benchmark.py benchmark-results/<arquivo>.json
```
