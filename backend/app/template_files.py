# app/template_files.py

EVALUATE_PY = """\
\"\"\"Évaluation offline : calcule metrics.json + figures SHAP / LIME.\"\"\" 

import argparse
import json
import logging
import yaml
from pathlib import Path

import torch
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from lime.lime_tabular import LimeTabularExplainer

import sys
# Monte le package « app » fourni par l’hôte (chemin /app)
if "/app" not in sys.path:
    sys.path.append("/app")

from model import MyModel                 # dans le template ZIP
from app.metrics.pipeline import analyze, _HAS_SHAP  # dispo dans l’image

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def evaluate(model_path: Path, test_csv: Path, config_path: Path, out_dir: Path):
    # ─── données + config ────────────────────────────────────────────────
    cfg_yaml = yaml.safe_load(open(config_path, encoding="utf-8"))
    df = pd.read_csv(test_csv)

    # on cherche un petit fichier JSON pour savoir quelles colonnes garder
    config_data_path = Path(config_path).parent / "config_data.json"
    if config_data_path.exists():
        cd = json.load(open(config_data_path, encoding="utf-8"))
        features = cd.get("features", list(df.columns))
        sensitive_attrs = cd.get("sensitive_attrs", [])
    else:
        # fallback : toutes les colonnes sauf la target
        features = [c for c in df.columns if c != cfg_yaml["target"]]
        sensitive_attrs = []

    X = df[features]

    # ─── y_true ────────────────────────────────────────────────────────────
    if cfg_yaml["task"] == "clustering":
        y_true = None
    else:
        # pour regression on garde les floats, pour classification on code 0…K-1
        y_series = df[cfg_yaml["target"]]
        if cfg_yaml["task"] == "classification":
            classes = sorted(y_series.unique())
            y_true = pd.Categorical(y_series, categories=classes).codes
        else:
            y_true = y_series.values

    # ─── modèle ──────────────────────────────────────────────────────────
    net = MyModel(input_dim=X.shape[1], hidden=cfg_yaml.get("hidden", 32))
    net.load_state_dict(torch.load(model_path, map_location="cpu"))
    net.eval()

    # ─── prédictions ─────────────────────────────────────────────────────
    with torch.no_grad():
        logits = net(torch.tensor(X.values, dtype=torch.float32))

    if cfg_yaml["task"] == "regression":
        y_pred = logits.view(-1).cpu().numpy()
    elif cfg_yaml["task"] == "classification":
        if logits.ndim == 1 or (logits.ndim == 2 and logits.size(1) == 1):
            probs = torch.sigmoid(logits.view(-1)).cpu().numpy()
            y_pred = probs
        else:
            y_pred = torch.softmax(logits, dim=1).cpu().numpy()
    else:  # clustering
        out_np = logits.cpu().numpy()
        y_pred = (
            out_np.argmax(axis=1)
            if (out_np.ndim > 1 and out_np.shape[1] > 1)
            else out_np
        )

    # ─── fonction de proba pour LIME ───────────────────────────────────────
    def predict_proba(x: np.ndarray) -> np.ndarray:
        with torch.no_grad():
            o = net(torch.tensor(x, dtype=torch.float32))
        if o.ndim == 1 or (o.ndim == 2 and o.size(1) == 1):
            p = torch.sigmoid(o.view(-1)).cpu().numpy()
            return np.vstack([1 - p, p]).T
        else:
            return torch.softmax(o, dim=1).cpu().numpy()

    # ─── analyse complète ────────────────────────────────────────────────
    if cfg_yaml["task"] == "clustering":
        metrics = analyze(y_pred=y_pred, y_true=None, X=X, sensitive_attrs=[])
    else:
        metrics = analyze(
            y_pred=y_pred,
            y_true=y_true,
            X=X,
            sensitive_attrs=sensitive_attrs,
            model=net,
            ref_stats_path=Path(config_path).parent / "ref_stats.csv",
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    metrics["task"]         = cfg_yaml["task"]
    metrics["model_name"]   = type(net).__name__
    metrics["dataset_size"] = len(df)

    # ─── SHAP global (top-10) ─────────────────────────────────────────────
    if _HAS_SHAP and "explainability" in metrics:
        shap_vals = metrics["explainability"]["mean_abs_shap_values"]
        top = sorted(shap_vals.items(), key=lambda x: x[1], reverse=True)[:10]
        feats, vals = zip(*top)

        shap_colors = [
            "#FF6F61", "#6B8E23", "#FFA500", "#DAA520", "#CD5C5C",
            "#8FBC8F", "#FF8C00", "#9ACD32", "#FF4500", "#D2691E"
        ]

        plt.figure()
        plt.barh(range(len(vals)), vals, color=shap_colors[:len(vals)])
        plt.yticks(range(len(vals)), feats)
        plt.xlabel("Mean |SHAP value|")
        plt.tight_layout()
        plt.savefig(out_dir / "shap_summary.png")
        plt.close()
        metrics.setdefault("explainability", {})["shap_summary_plot"] = str(out_dir / "shap_summary.png")

    # ─── LIME locale (classification) ────────────────────────────────────
    if cfg_yaml["task"] == "classification":
        try:
            explainer = LimeTabularExplainer(
                training_data=X.values,
                feature_names=list(X.columns),
                mode="classification",
                discretize_continuous=True,
            )
            exp = explainer.explain_instance(X.values[0], predict_proba, num_features=10)
            fig = exp.as_pyplot_figure()
            ax = fig.gca()

            lime_colors = [
                "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
                "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
            ]

            bars = ax.patches
            for bar, color in zip(bars, lime_colors):
                bar.set_color(color)

            fig.savefig(out_dir / "lime_local.png")
            plt.close(fig)
            metrics.setdefault("explainability", {})["lime_local_plot"] = str(out_dir / "lime_local.png")
        except Exception:
            log.exception("LIME explanation failed")

   # ─── flatten summary ────────────────────────────────────────────────
    perf = metrics.get("performance", {})
    # classification → keep accuracy
    if "accuracy" in perf:
        metrics["accuracy"] = perf["accuracy"]
    # regression → store R² under its own name
    if "r2" in perf:
        metrics["r2"] = perf["r2"]

    # ─── export JSON ─────────────────────────────────────────────────────
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model",  required=True)
    p.add_argument("--test",   required=True)
    p.add_argument("--config", required=True)
    p.add_argument("--out",    required=True)
    args = p.parse_args()
    evaluate(Path(args.model), Path(args.test), Path(args.config), Path(args.out))

"""
