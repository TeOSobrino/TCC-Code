# Integração do modelo FL-NIDS CNN/FedAvg

O projeto do GitHub pode ser integrado ao testbed, mas o ZIP analisado não contém `fl_model.h5`.
Ele contém apenas:
- `FL-Based_NIDS.py`
- CSVs UNSW-NB15
- `dataPre.py`

## 1. Gerar o modelo treinado

No repositório original:

```bash
mkdir -p Server CentralServer
python FL-Based_NIDS.py
```

Ao final, deve existir:

```bash
CentralServer/fl_model.h5
```

## 2. Copiar o modelo para o cluster

No projeto k3s:

```bash
./scripts/deploy.sh
./scripts/copy-model-to-pvc.sh /caminho/para/CentralServer/fl_model.h5
```

## 3. Ativar o modelo real

```bash
kubectl -n pcap-testbed set env deployment/ids-agent MODEL_BACKEND=flnids
kubectl -n pcap-testbed set env deployment/ids-agent MODEL_ENABLED=true
```

## 4. Desativar o modelo, mantendo captura

```bash
kubectl -n pcap-testbed set env deployment/ids-agent MODEL_ENABLED=false
```

## 5. Voltar ao dummy

```bash
kubectl -n pcap-testbed set env deployment/ids-agent MODEL_BACKEND=dummy
kubectl -n pcap-testbed set env deployment/ids-agent MODEL_ENABLED=true
```

## Limitação importante

O modelo espera entrada com shape:

```python
(1, 4, 196)
```

Ou seja:
- janela temporal `TL=4`;
- 196 features;
- features compatíveis com o pré-processamento do UNSW-NB15.

O adaptador atual cria uma entrada estruturalmente compatível, mas ainda não semanticamente equivalente ao UNSW-NB15.
Para uma avaliação válida, substitua `extract_dummy_features` e `_vector_from_features` por um extrator real de features de fluxo.
