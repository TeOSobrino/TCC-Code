# Segurança em IoT: Detecção de Ataques com Aprendizado Federado em Ambientes de Borda

k3s PCAP Replay Testbed com IDS Federado

Projeto para simular tráfego de datasets UNSW-NB15, CIC-IDS2017 e CIC-IDS2018 em um cluster k3s, usando:
- `tcpreplay` para reproduzir PCAPs em tempo quase real;
- `tcpdump` para captura;
- agentes IDS locais;
- servidor central dummy;
- chave `MODEL_ENABLED=true/false` para ligar/desligar o modelo.

> Este projeto não implementa o modelo final do TCC. Ele cria a infraestrutura para encaixar FLiForest, SSFL, IFCEA ou outro modelo posteriormente.

## Estrutura esperada dos PCAPs

Coloque os PCAPs em:

```bash
datasets/
├── UNSW-NB15/
│   └── sample.pcap
├── CIC-IDS2017/
│   └── sample.pcap
└── CIC-IDS2018/
    └── sample.pcap
```

## Subir ambiente local

```bash
./scripts/setup-k3s.sh
./scripts/build-images.sh
./scripts/deploy.sh
```

## Ligar/desligar modelo

```bash
# Liga inferência dummy
kubectl -n pcap-testbed set env deployment/ids-agent MODEL_ENABLED=true

# Desliga inferência dummy, mantendo captura e envio de logs
kubectl -n pcap-testbed set env deployment/ids-agent MODEL_ENABLED=false
```

## Reproduzir tráfego

```bash
kubectl -n pcap-testbed create job --from=cronjob/pcap-replay-unsw replay-unsw-manual
kubectl -n pcap-testbed create job --from=cronjob/pcap-replay-cic2017 replay-cic2017-manual
kubectl -n pcap-testbed create job --from=cronjob/pcap-replay-cic2018 replay-cic2018-manual
```

## Ver logs

```bash
kubectl -n pcap-testbed logs -l app=ids-agent -f
kubectl -n pcap-testbed logs -l app=fl-server -f
```
