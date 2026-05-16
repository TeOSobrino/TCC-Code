import os
import numpy as np
from pathlib import Path
from tensorflow import keras

TL = int(os.getenv("MODEL_TL", "4"))
FEATURES = int(os.getenv("MODEL_FEATURES", "196"))
MODEL_PATH = Path(os.getenv("MODEL_PATH", "/models/fl_model.h5"))
THRESHOLD = float(os.getenv("ANOMALY_THRESHOLD", "0.5"))


class FLNIDSModel:
    """
    Adaptador para o modelo CNN/FedAvg do projeto:
    Federated-Learning-Based-Intrusion-Detection-System.

    Entrada esperada pelo modelo:
        shape = (batch, 4, 196)

    Observação:
        Este adaptador assume que as features já estão no mesmo formato
        dos CSVs UNSW-NB15 usados no treinamento.
    """

    def __init__(self):
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Modelo não encontrado em {MODEL_PATH}. "
                "Monte o arquivo fl_model.h5 no volume /models."
            )

        self.model = keras.models.load_model(str(MODEL_PATH))
        self.buffer = []

    def _vector_from_features(self, features: dict) -> np.ndarray:
        """
        Conversor temporário.

        No projeto final, substitua esta função por um extrator real que gere
        as mesmas 196 features do UNSW-NB15.

        Aqui mantemos compatibilidade estrutural, mas não semântica.
        """
        vector = np.zeros((FEATURES,), dtype=np.float32)

        # Campos dummy vindos do agente atual.
        vector[0] = float(features.get("bytes", 0))
        vector[1] = float(features.get("packets_estimate", 0))

        # Normalização simples de segurança para evitar valores gigantes.
        # No modelo final, use o scaler salvo do treinamento.
        vector[0] = min(vector[0] / 5_000_000.0, 1.0)
        vector[1] = min(vector[1] / 50_000.0, 1.0)

        return vector

    def predict(self, features: dict) -> dict:
        vector = self._vector_from_features(features)
        self.buffer.append(vector)

        # Mantém janela temporal TL=4, repetindo a última amostra se necessário.
        while len(self.buffer) < TL:
            self.buffer.append(vector)

        self.buffer = self.buffer[-TL:]
        x = np.array(self.buffer, dtype=np.float32).reshape(1, TL, FEATURES)

        score = float(self.model.predict(x, verbose=0)[0][0])
        label = "anomaly" if score >= THRESHOLD else "normal"

        return {
            "model": "flnids-cnn-fedavg",
            "enabled": True,
            "anomaly_score": round(score, 6),
            "label": label,
            "threshold": THRESHOLD,
            "input_shape": [1, TL, FEATURES]
        }
