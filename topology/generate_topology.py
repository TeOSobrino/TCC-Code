#!/usr/bin/env python3
import argparse
from pathlib import Path
import yaml


def service(name, ns, selector, port, target):
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": name, "namespace": ns},
        "spec": {
            "selector": selector,
            "ports": [{"name": "http", "port": port, "targetPort": target}],
        },
    }


def pvc(name, ns, size):
    return {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {"name": name, "namespace": ns},
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "resources": {"requests": {"storage": size}},
        },
    }


def resource_spec(cfg, role):
    return cfg.get("resources", {}).get(role, {})


def distribute_iot(n, m):
    groups = [[] for _ in range(m)]
    for i in range(n):
        groups[i % m].append(i)
    return groups


def central_deployment(cfg):
    ns = cfg["namespace"]
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": "central-server", "namespace": ns, "labels": {"role": "central"}},
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"app": "central-server"}},
            "template": {
                "metadata": {"labels": {"app": "central-server", "role": "central"}},
                "spec": {
                    "containers": [{
                        "name": "central-server",
                        "image": cfg["images"]["central_server"],
                        "imagePullPolicy": "IfNotPresent",
                        "ports": [{"containerPort": 8080}],
                        "resources": resource_spec(cfg, "central"),
                    }]
                },
            },
        },
    }


def edge_deployment(cfg, edge_id, children):
    ns = cfg["namespace"]
    name = f"edge-{edge_id}"
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": name,
            "namespace": ns,
            "labels": {"role": "edge", "edge-id": str(edge_id)},
        },
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"app": name}},
            "template": {
                "metadata": {
                    "labels": {"app": name, "role": "edge", "edge-id": str(edge_id)}
                },
                "spec": {
                    "containers": [{
                        "name": "edge-node",
                        "image": cfg["images"]["edge_node"],
                        "imagePullPolicy": "IfNotPresent",
                        "ports": [{"containerPort": 8081}],
                        "env": [
                            {"name": "EDGE_ID", "value": name},
                            {"name": "PARENT_SERVER_URL", "value": "http://central-server:8080"},
                            {"name": "CHILDREN", "value": ",".join([f"iot-{i}" for i in children])},
                        ],
                        "resources": resource_spec(cfg, "edge"),
                    }]
                },
            },
        },
    }


def iot_deployment(cfg, iot_id, edge_id):
    ns = cfg["namespace"]
    name = f"iot-{iot_id}"
    edge_name = f"edge-{edge_id}"
    model = cfg["model"]
    capture = cfg["capture"]
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": name,
            "namespace": ns,
            "labels": {"role": "iot", "parent-edge": edge_name},
        },
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"app": name}},
            "template": {
                "metadata": {
                    "labels": {"app": name, "role": "iot", "parent-edge": edge_name}
                },
                "spec": {
                    "containers": [{
                        "name": "ids-agent",
                        "image": cfg["images"]["iot_agent"],
                        "imagePullPolicy": "IfNotPresent",
                        "securityContext": {
                            "capabilities": {"add": ["NET_RAW", "NET_ADMIN"]}
                        },
                        "env": [
                            {"name": "DEVICE_ID", "value": name},
                            {"name": "PARENT_EDGE_ID", "value": edge_name},
                            {"name": "SERVER_URL", "value": f"http://{edge_name}:8081"},
                            {"name": "CAPTURE_INTERFACE", "value": str(capture.get("interface", "eth0"))},
                            {"name": "CAPTURE_SECONDS", "value": str(capture.get("seconds", 20))},
                            {"name": "MODEL_ENABLED", "value": str(model.get("enabled", True)).lower()},
                            {"name": "MODEL_BACKEND", "value": str(model.get("backend", "dummy"))},
                            {"name": "MODEL_PATH", "value": str(model.get("path", "/models/fl_model.h5"))},
                            {"name": "MODEL_TL", "value": str(model.get("tl", 4))},
                            {"name": "MODEL_FEATURES", "value": str(model.get("features", 196))},
                            {"name": "ANOMALY_THRESHOLD", "value": str(model.get("anomaly_threshold", 0.5))},
                        ],
                        "volumeMounts": [
                            {"name": "captures", "mountPath": "/captures"},
                            {"name": "models", "mountPath": "/models"},
                        ],
                        "resources": resource_spec(cfg, "iot"),
                    }],
                    "volumes": [
                        {"name": "captures", "persistentVolumeClaim": {"claimName": "captures-pvc"}},
                        {"name": "models", "persistentVolumeClaim": {"claimName": "models-pvc"}},
                    ],
                },
            },
        },
    }


def cronjob_replayer(cfg, dataset):
    ns = cfg["namespace"]
    safe = dataset["name"].lower().replace("_", "-").replace("/", "-")
    return {
        "apiVersion": "batch/v1",
        "kind": "CronJob",
        "metadata": {"name": f"pcap-replay-{safe}", "namespace": ns},
        "spec": {
            "schedule": "*/30 * * * *",
            "suspend": True,
            "jobTemplate": {
                "spec": {
                    "template": {
                        "spec": {
                            "restartPolicy": "Never",
                            "containers": [{
                                "name": "replayer",
                                "image": cfg["images"]["pcap_replayer"],
                                "imagePullPolicy": "IfNotPresent",
                                "securityContext": {
                                    "capabilities": {"add": ["NET_RAW", "NET_ADMIN"]}
                                },
                                "env": [
                                    {"name": "DATASET", "value": dataset["name"]},
                                    {"name": "PCAP_FILE", "value": dataset["pcap_file"]},
                                    {"name": "LOOP", "value": "1"},
                                    {"name": "PPS", "value": str(dataset.get("pps", 200))},
                                ],
                                "volumeMounts": [{"name": "datasets", "mountPath": "/datasets"}],
                            }],
                            "volumes": [
                                {"name": "datasets", "persistentVolumeClaim": {"claimName": "datasets-pvc"}}
                            ],
                        }
                    }
                }
            },
        },
    }


def dump_many(path, docs):
    path.write_text("---\n".join(yaml.safe_dump(d, sort_keys=False, allow_unicode=True) for d in docs), encoding="utf-8")


def topology_md(cfg, groups):
    lines = ["# Topologia gerada", "", "```text", "central-server"]
    for edge_id, children in enumerate(groups):
        ep = "└──" if edge_id == len(groups) - 1 else "├──"
        lines.append(f"{ep} edge-{edge_id}")
        for idx, iot in enumerate(children):
            cp = "    └──" if idx == len(children) - 1 else "    ├──"
            lines.append(f"{cp} iot-{iot}")
    lines += [
        "```",
        "",
        f"- Dispositivos IoT: {cfg['iot_devices']}",
        f"- Nós de borda: {cfg['edge_nodes']}",
        "- Comunicação lógica: `iot-X → edge-Y → central-server`",
    ]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="topology/topology.yaml")
    ap.add_argument("--out", default="k8s/generated")
    ap.add_argument("--iot-devices", type=int)
    ap.add_argument("--edge-nodes", type=int)
    ap.add_argument("--model-backend")
    ap.add_argument("--model-enabled")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if args.iot_devices is not None:
        cfg["iot_devices"] = args.iot_devices
    if args.edge_nodes is not None:
        cfg["edge_nodes"] = args.edge_nodes
    if args.model_backend is not None:
        cfg["model"]["backend"] = args.model_backend
    if args.model_enabled is not None:
        cfg["model"]["enabled"] = args.model_enabled.lower() == "true"

    n = int(cfg["iot_devices"])
    m = int(cfg["edge_nodes"])
    if n < 1 or m < 1:
        raise SystemExit("iot_devices e edge_nodes precisam ser >= 1")
    if m > n:
        raise SystemExit("edge_nodes não deve ser maior que iot_devices nesta versão")

    groups = distribute_iot(n, m)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    dump_many(out / "00-namespace.yaml", [{"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": cfg["namespace"]}}])
    dump_many(out / "01-pvc.yaml", [
        pvc("datasets-pvc", cfg["namespace"], "20Gi"),
        pvc("captures-pvc", cfg["namespace"], "20Gi"),
        pvc("models-pvc", cfg["namespace"], "2Gi"),
    ])
    dump_many(out / "02-central.yaml", [
        central_deployment(cfg),
        service("central-server", cfg["namespace"], {"app": "central-server"}, 8080, 8080),
    ])
    edge_docs = []
    for eid, children in enumerate(groups):
        edge_docs.append(edge_deployment(cfg, eid, children))
        edge_docs.append(service(f"edge-{eid}", cfg["namespace"], {"app": f"edge-{eid}"}, 8081, 8081))
    dump_many(out / "03-edges.yaml", edge_docs)

    iot_docs = []
    for eid, children in enumerate(groups):
        for iot in children:
            iot_docs.append(iot_deployment(cfg, iot, eid))
    dump_many(out / "04-iot-devices.yaml", iot_docs)

    dump_many(out / "05-replayers.yaml", [cronjob_replayer(cfg, d) for d in cfg.get("datasets", [])])
    (out / "TOPOLOGY.md").write_text(topology_md(cfg, groups), encoding="utf-8")

    print(f"[OK] Manifests gerados em {out}")
    print(f"[OK] Topologia: {n} dispositivos IoT, {m} nós de borda")


if __name__ == "__main__":
    main()
