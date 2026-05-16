
#!/usr/bin/env python3
# Uso:
#   python gerar_metricas.py IFCEA-20-4.json SSFL-20-4.json FliForest-20-4.json
#
# Saídas:
#   metricas-geradas/metricas_agregadas.json
#   metricas-geradas/tabela_metricas.csv
#   metricas-geradas/tabela_metricas.md
#   metricas-geradas/*.png

import json
import sys
import re
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, List, Optional

import pandas as pd
import matplotlib.pyplot as plt


def parse_filename(path: str) -> Dict[str, Any]:
    name = Path(path).stem
    match = re.match(r"(.+)-(\d+)-(\d+)$", name)

    if not match:
        raise ValueError(
            f"Nome inválido: {path}. Use: [Modelo]-[Numero disp]-[Numero Nós].json"
        )

    return {
        "modelo": match.group(1),
        "dispositivos": int(match.group(2)),
        "nos_borda": int(match.group(3)),
    }


def load_events(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        if "events" in data and isinstance(data["events"], list):
            return data["events"]
        return [data]

    raise ValueError(f"Formato JSON inválido em {path}")


def get_nested(d: Dict[str, Any], *keys: str) -> Optional[Any]:
    cur = d
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def normalize_label(value: Any) -> Optional[str]:
    if value is None:
        return None

    value = str(value).lower().strip()

    if value in {"normal", "benign", "0", "false"}:
        return "normal"

    if value in {"anomaly", "anomalous", "attack", "malicious", "1", "true"}:
        return "anomaly"

    return value


def extract_true_label(event: Dict[str, Any]) -> Optional[str]:
    candidates = [
        get_nested(event, "true_label"),
        get_nested(event, "ground_truth"),
        get_nested(event, "label"),
        get_nested(event, "features", "true_label"),
        get_nested(event, "features", "ground_truth"),
        get_nested(event, "features", "label"),
    ]

    for c in candidates:
        label = normalize_label(c)
        if label is not None:
            return label

    return None


def extract_pred_label(event: Dict[str, Any]) -> Optional[str]:
    candidates = [
        get_nested(event, "prediction", "label"),
        get_nested(event, "predicted_label"),
        get_nested(event, "prediction"),
    ]

    for c in candidates:
        label = normalize_label(c)
        if label is not None and label != "not_evaluated":
            return label

    return None


def safe_number(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def summarize_file(path: str) -> Dict[str, Any]:
    meta = parse_filename(path)
    events = load_events(path)

    inference_ms = []
    feature_ms = []
    capture_ms = []
    cycle_ms = []
    bytes_values = []

    y_true = []
    y_pred = []

    for ev in events:
        metrics = ev.get("metrics", {})
        features = ev.get("features", {})

        for arr, key in [
            (inference_ms, "inference_ms"),
            (feature_ms, "feature_ms"),
            (capture_ms, "capture_ms"),
            (cycle_ms, "cycle_ms"),
        ]:
            value = safe_number(metrics.get(key))
            if value is not None:
                arr.append(value)

        b = safe_number(features.get("bytes"))
        if b is not None:
            bytes_values.append(b)

        true_label = extract_true_label(ev)
        pred_label = extract_pred_label(ev)

        if true_label is not None and pred_label is not None:
            y_true.append(true_label)
            y_pred.append(pred_label)

    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = correct / len(y_true) if y_true else None

    tp = sum(1 for t, p in zip(y_true, y_pred) if t == "anomaly" and p == "anomaly")
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == "normal" and p == "normal")
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == "normal" and p == "anomaly")
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == "anomaly" and p == "normal")

    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and (precision + recall) > 0
        else None
    )

    def avg(values: List[float]) -> Optional[float]:
        return mean(values) if values else None

    def med(values: List[float]) -> Optional[float]:
        return median(values) if values else None

    return {
        **meta,
        "arquivo": Path(path).name,
        "eventos": len(events),
        "amostras_com_rotulo": len(y_true),
        "acuracia": accuracy,
        "precisao": precision,
        "recall": recall,
        "f1_score": f1,
        "verdadeiros_positivos": tp,
        "verdadeiros_negativos": tn,
        "falsos_positivos": fp,
        "falsos_negativos": fn,
        "overhead_inferencia_ms_medio": avg(inference_ms),
        "overhead_inferencia_ms_mediano": med(inference_ms),
        "feature_ms_medio": avg(feature_ms),
        "capture_ms_medio": avg(capture_ms),
        "cycle_ms_medio": avg(cycle_ms),
        "bytes_medio": avg(bytes_values),
    }


def bar_plot(df: pd.DataFrame, column: str, ylabel: str, title: str, output: Path) -> None:
    plot_df = df.dropna(subset=[column])

    if plot_df.empty:
        print(f"[AVISO] Sem dados para gráfico: {title}")
        return

    plt.figure(figsize=(9, 5))
    plt.bar(plot_df["modelo"], plot_df[column])
    plt.xlabel("Modelo")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(output, dpi=300)
    plt.close()


def grouped_overhead_plot(df: pd.DataFrame, out_dir: Path) -> None:
    cols = [
        "overhead_inferencia_ms_medio",
        "feature_ms_medio",
        "capture_ms_medio",
        "cycle_ms_medio",
    ]

    available = [c for c in cols if c in df.columns and df[c].notna().any()]

    if not available:
        return

    plot_df = df.set_index("modelo")[available]

    plt.figure(figsize=(11, 6))
    plot_df.plot(kind="bar", ax=plt.gca())
    plt.xlabel("Modelo")
    plt.ylabel("Tempo médio (ms)")
    plt.title("Comparação de overhead médio por modelo")
    plt.xticks(rotation=0)
    plt.tight_layout()

    output = out_dir / "grafico_overhead_agrupado.png"
    plt.savefig(output, dpi=300)
    plt.close()


def main() -> None:
    if len(sys.argv) != 4:
        print("Uso: python gerar_metricas.py <arquivo1> <arquivo2> <arquivo3>")
        sys.exit(1)

    arquivos = sys.argv[1:]

    out_dir = Path("metricas-geradas")
    out_dir.mkdir(exist_ok=True)

    rows = [summarize_file(a) for a in arquivos]
    df = pd.DataFrame(rows)

    ordered_cols = [
        "modelo",
        "dispositivos",
        "nos_borda",
        "eventos",
        "amostras_com_rotulo",
        "acuracia",
        "precisao",
        "recall",
        "f1_score",
        "verdadeiros_positivos",
        "verdadeiros_negativos",
        "falsos_positivos",
        "falsos_negativos",
        "overhead_inferencia_ms_medio",
        "overhead_inferencia_ms_mediano",
        "feature_ms_medio",
        "capture_ms_medio",
        "cycle_ms_medio",
        "bytes_medio",
        "arquivo",
    ]

    df = df[[c for c in ordered_cols if c in df.columns]]

    csv_path = out_dir / "tabela_metricas.csv"
    md_path = out_dir / "tabela_metricas.md"
    json_path = out_dir / "metricas_agregadas.json"

    df.to_csv(csv_path, index=False)
    df.to_markdown(md_path, index=False)

    payload = {
        "arquivos_entrada": [str(Path(a).name) for a in arquivos],
        "metricas": df.where(pd.notnull(df), None).to_dict(orient="records"),
        "melhor_acuracia": (
            df.loc[df["acuracia"].idxmax()].to_dict()
            if "acuracia" in df.columns and df["acuracia"].notna().any()
            else None
        ),
        "menor_overhead_inferencia": (
            df.loc[df["overhead_inferencia_ms_medio"].idxmin()].to_dict()
            if "overhead_inferencia_ms_medio" in df.columns and df["overhead_inferencia_ms_medio"].notna().any()
            else None
        ),
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    bar_plot(
        df,
        "overhead_inferencia_ms_medio",
        "Overhead médio de inferência (ms)",
        "Overhead médio de inferência por modelo",
        out_dir / "grafico_overhead_inferencia.png",
    )

    bar_plot(
        df,
        "cycle_ms_medio",
        "Tempo médio do ciclo completo (ms)",
        "Tempo médio do ciclo completo por modelo",
        out_dir / "grafico_ciclo_completo.png",
    )

    bar_plot(
        df,
        "acuracia",
        "Acurácia",
        "Acurácia por modelo",
        out_dir / "grafico_acuracia.png",
    )

    grouped_overhead_plot(df, out_dir)

    print(df.to_string(index=False))
    print(f"\n[OK] Métricas agregadas: {json_path}")
    print(f"[OK] Tabela CSV: {csv_path}")
    print(f"[OK] Tabela Markdown: {md_path}")


if __name__ == "__main__":
    main()
