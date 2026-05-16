# Pasta para o modelo real

Substitua o dummy em `agent/agent.py` por uma chamada ao seu modelo.

Sugestão de interface:

```python
class Detector:
    def __init__(self, model_path: str):
        ...

    def predict(self, features: dict) -> dict:
        return {
            "anomaly_score": 0.0,
            "label": "normal"
        }
```

A variável `MODEL_ENABLED` deve continuar existindo para permitir comparação:

- `MODEL_ENABLED=true`: roda o modelo;
- `MODEL_ENABLED=false`: captura tráfego, extrai features e envia logs sem classificar.
```
