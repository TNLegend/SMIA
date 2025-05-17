"""Évaluation offline : calcule metrics.json + figures SHAP / LIME.""" 

import argparse
import json
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


def evaluate(model_path: Path, test_csv: Path, config_path: Path, out_dir: Path):
    # ─── données + config ────────────────────────────────────────────────
    cfg_yaml = yaml.safe_load(open(config_path))
    df = pd.read_csv(test_csv)

    # on cherche un petit fichier JSON pour savoir quelles colonnes garder
    config_data_path = Path(config_path).parent / "config_data.json"
    if config_data_path.exists():
        cd = json.load(open(config_data_path))
        features = cd.get("features", list(df.columns))
        sensitive_attrs = cd.get("sensitive_attrs", [])
    else:
        # fallback : toutes les colonnes sauf la target
        features = [c for c in df.columns if c != cfg_yaml["target"]]
        sensitive_attrs = []

    X = df[features]
    y_true = df[cfg_yaml["target"]]


    # ─── modèle ──────────────────────────────────────────────────────────
    net = MyModel(input_dim=X.shape[1], hidden=cfg_yaml["hidden"])
    net.load_state_dict(torch.load(model_path, map_location="cpu"))
    net.eval()

    # prédictions
    with torch.no_grad():
        logits = net(torch.tensor(X.values, dtype=torch.float32)).flatten()
        y_prob = torch.sigmoid(logits).cpu().numpy()          # vraies probabilités
    y_pred = (y_prob > 0.5).astype(int)

    # fonction de proba pour LIME (fermée sur net)
    def predict_proba(x: np.ndarray) -> np.ndarray:
        with torch.no_grad():
            l = net(torch.tensor(x, dtype=torch.float32)).flatten()
            p = torch.sigmoid(l).cpu().numpy()
        return np.vstack([1 - p, p]).T                        # shape (n,2)

    # ─── analyse complète ────────────────────────────────────────────────
    metrics = analyze(
        y_pred,
        y_true,
        X,
        sensitive_attrs=sensitive_attrs,
        cfg=None,
        model=net,
        ref_stats_path=Path(config_path).parent / "ref_stats.csv",
    )

    out_dir.mkdir(parents=True, exist_ok=True)

    # ─── SHAP global (top-10) ────────────────────────────────────────────
    if _HAS_SHAP and "explainability" in metrics:
        shap_vals = metrics["explainability"]["mean_abs_shap_values"]
        top = sorted(shap_vals.items(), key=lambda x: x[1], reverse=True)[:10]
        feats, vals = zip(*top)
        plt.figure()
        plt.barh(range(len(vals)), vals)
        plt.yticks(range(len(vals)), feats)
        plt.xlabel("Mean |SHAP value|")
        plt.tight_layout()
        plt.savefig(out_dir / "shap_summary.png")
        plt.close()
        # on enregistre aussi le chemin du plot dans les métriques
        metrics.setdefault("explainability", {})["shap_summary_plot"] = str(out_dir / "shap_summary.png")
    

    # ─── LIME locale (première ligne) ────────────────────────────────────
    try:
        explainer = LimeTabularExplainer(
            training_data=X.values,
            feature_names=list(X.columns),
            mode="classification",
            discretize_continuous=True,
        )
        exp = explainer.explain_instance(
            X.values[0], predict_proba, num_features=10
        )
        fig = exp.as_pyplot_figure()
        fig.savefig(out_dir / "lime_local.png")
        plt.close(fig)
        metrics.setdefault("explainability", {})["lime_local_plot"] = str(out_dir / "lime_local.png")
    except Exception:
        # on ignore les échecs de LIME pour ne pas faire planter l'ensemble
        pass

    # ─── export JSON ─────────────────────────────────────────────────────
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model",  required=True)
    p.add_argument("--test",   required=True)
    p.add_argument("--config", required=True)
    p.add_argument("--out",    required=True)
    args = p.parse_args()
    evaluate(Path(args.model), Path(args.test), Path(args.config), Path(args.out))
