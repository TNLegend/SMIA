# app/metrics/pipeline.py
from __future__ import annotations

import itertools
import logging
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler

log = logging.getLogger(__name__)

# ─────────────────────────── optional deps ────────────────────────────
try:
    import shap  # type: ignore
    _HAS_SHAP = True
except ImportError:
    _HAS_SHAP = False
    shap = None  # type: ignore

try:
    from alibi_detect.cd import KSDrift  # type: ignore
    _HAS_ALIBI = True
except ImportError:
    _HAS_ALIBI = False
    KSDrift = None  # type: ignore

try:
    import torchattacks as ta  # type: ignore
    _HAS_ATTACKS = True
except ImportError:
    _HAS_ATTACKS = False
    ta = None  # type: ignore

try:
    from fairlearn.metrics import (
        demographic_parity_difference,
        equalized_odds_difference,
    )
    _HAS_FAIRLEARN = True
except ImportError:
    _HAS_FAIRLEARN = False

try:
    from evidently.profile import Profile
    from evidently.profile.sections import DataDriftProfileSection
    from evidently.dashboard import Dashboard
    from evidently.dashboard.tabs import DataDriftTab
    _HAS_EVIDENTLY = True
except ImportError:
    _HAS_EVIDENTLY = False


def _compute_classification_performance(
    y_true: np.ndarray, y_prob: np.ndarray, y_pred: np.ndarray
) -> Dict[str, float]:
    unique_classes = np.unique(y_true)
    if set(unique_classes) <= {0, 1}:
        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1": float(f1_score(y_true, y_pred, zero_division=0)),
            "auc": float(roc_auc_score(y_true, y_prob)),
            "mse": float(mean_squared_error(y_true, y_prob)),
        }
    else:
        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
            "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
            "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
            "auc_ovr": float(roc_auc_score(y_true, y_prob, multi_class="ovr")),
        }


def _compute_regression_performance(
    y_true: np.ndarray, y_pred: np.ndarray
) -> Dict[str, float]:
    return {
        "mse": float(mean_squared_error(y_true, y_pred)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }


def _performance_by_group(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    X: pd.DataFrame,
    group_cols: List[str],
) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    for col in group_cols:
        if col not in X.columns:
            continue
        for value in X[col].unique():
            mask = X[col] == value
            if not mask.any():
                continue
            key = f"{col}={value}"
            avg = "binary" if set(np.unique(y_true)) <= {0, 1} else "macro"
            out[key] = {
                "support": int(mask.sum()),
                "accuracy": float(accuracy_score(y_true[mask], y_pred[mask])),
                "f1": float(f1_score(y_true[mask], y_pred[mask], average=avg, zero_division=0)),
            }
    return out


def _parity_metrics(
    y_pred: np.ndarray, group: np.ndarray
) -> Tuple[float, float]:
    pr_1 = y_pred[group == 1].mean()
    pr_0 = y_pred[group == 0].mean()
    spd = pr_1 - pr_0
    di = float(pr_1 / pr_0) if pr_0 else np.nan
    return spd, di


def _equal_opportunity(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    group: np.ndarray,
) -> float:
    mask1, mask0 = group == 1, group == 0
    tpr1 = recall_score(y_true[mask1], y_pred[mask1], zero_division=0)
    tpr0 = recall_score(y_true[mask0], y_pred[mask0], zero_division=0)
    return tpr1 - tpr0


def _predictive_parity(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    group: np.ndarray,
) -> float:
    mask1, mask0 = group == 1, group == 0
    ppv1 = precision_score(y_true[mask1], y_pred[mask1], zero_division=0)
    ppv0 = precision_score(y_true[mask0], y_pred[mask0], zero_division=0)
    return ppv1 - ppv0


def _fairness_for_attr(
    attr: str,
    X: pd.DataFrame,
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> Dict[str, float]:
    if attr not in X.columns:
        return {"error": "column missing"}
    series = X[attr]
    if series.dtype.kind in "O":
        group = (series == series.unique()[0]).astype(int).values
    else:
        group = (series > series.median()).astype(int).values
    spd, di = _parity_metrics(y_pred, group)
    return {
        "statistical_parity_diff": spd,
        "disparate_impact": di,
        "equal_opportunity_diff": _equal_opportunity(y_true, y_pred, group),
        "predictive_parity_diff": _predictive_parity(y_true, y_pred, group),
    }


def _fairness_intersectional(
    attrs: List[str],
    X: pd.DataFrame,
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> Dict[str, Dict[str, float]]:
    results: Dict[str, Dict[str, float]] = {}
    for a, b in itertools.combinations(attrs, 2):
        if a not in X.columns or b not in X.columns:
            continue
        inter = (X[a].astype(str) + "_" + X[b].astype(str)).astype("category")
        for level in inter.unique():
            mask = inter == level
            key = f"{a}&{b}={level}"
            results[key] = {
                "support": int(mask.sum()),
                "accuracy": float(accuracy_score(y_true[mask], y_pred[mask])),
                "positive_rate": float(y_pred[mask].mean()),
            }
    return results


def _shap_global_importance(model, X: pd.DataFrame, nsample: int = 500):
    if not _HAS_SHAP:
        return None
    try:
        import shap
        import torch

        # Black-box wrapper: NumPy → NumPy
        def predict_np(x: np.ndarray) -> np.ndarray:
            with torch.no_grad():
                t = torch.tensor(x, dtype=torch.float32)
                out = model(t).cpu().numpy()
            # regression or binary (logits dim=1) → return 1-d array
            if out.ndim == 1 or (out.ndim == 2 and out.shape[1] == 1):
                return out.reshape(-1)
            # multiclass → return shape (n_samples, n_classes)
            return out

        # small background dataset for speed
        bg = shap.sample(X.values, min(100, len(X)), random_state=0)
        explainer = shap.KernelExplainer(predict_np, bg)

        subset = X.sample(n=min(nsample, len(X)), random_state=0).values
        shap_vals = explainer.shap_values(subset, nsample=nsample)

        # shap_vals is either an array (regression/binary) or list of arrays (multiclass)
        if isinstance(shap_vals, list):
            abs_means = [np.abs(arr).mean(axis=0) for arr in shap_vals]
            abs_mean = np.mean(abs_means, axis=0)
        else:
            abs_mean = np.abs(shap_vals).mean(axis=0)

        return dict(zip(X.columns, abs_mean.tolist()))
    except Exception:
        log.exception("SHAP explanation failed")
        return None




def _compute_psi(hist_ref: np.ndarray, hist_new: np.ndarray, epsilon: float = 1e-6) -> float:
    hr = hist_ref + epsilon
    hn = hist_new + epsilon
    hr = hr / hr.sum()
    hn = hn / hn.sum()
    return float(np.sum((hn - hr) * np.log(hn / hr)))


def _compute_drift(
    X_test: pd.DataFrame,
    ref_stats_path: Union[str, Path],
) -> Optional[Dict[str, Any]]:
    if not Path(ref_stats_path).exists():
        return None
    drift: Dict[str, Any] = {}
    ref_df = pd.read_csv(ref_stats_path)

    # 1) PSI on numeric only
    psi_vals = {}
    numeric_cols = X_test.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        hist_ref, bins = np.histogram(ref_df[col], bins=10, density=False)
        hist_new, _ = np.histogram(X_test[col], bins=bins, density=False)
        psi_vals[col] = _compute_psi(hist_ref, hist_new)
    drift["psi"] = psi_vals

    # 2) KS drift
    if _HAS_ALIBI:
        try:
            ref_vals = ref_df[numeric_cols].values
            scaler = StandardScaler().fit(ref_vals)  # fitted on a plain array
            ks = KSDrift(
                ref_vals,
                p_val=0.05,
                preprocess_fn=scaler.transform,  # also returns a plain array
            )
            preds = ks.predict(X_test[numeric_cols].values, drift_type="batch")
            p_arr = preds["data"]["p_val"]
            drift["ks_drift"] = {
                "is_drift": bool(preds["data"]["is_drift"]),
                "p_value": float(p_arr[0]) if hasattr(p_arr, "__len__") else float(p_arr),
            }
        except Exception:
            log.exception("KS drift test failed")

        # 3) Evidently report
        if _HAS_EVIDENTLY:
            try:
                profile = Profile(sections=[DataDriftProfileSection()])
                profile.calculate(ref_df[numeric_cols], X_test[numeric_cols])
                drift["evidently_profile"] = profile.json()

                report_dir = Path(ref_stats_path).parent
                report_path = report_dir / "drift_report.html"
                dashboard = Dashboard(tabs=[DataDriftTab()])
                dashboard.calculate(ref_df[numeric_cols], X_test[numeric_cols])
                dashboard.save_html(str(report_path))
                drift["evidently_report"] = str(report_path)
            except Exception:
                log.exception("Evidently drift report failed")

    return drift or None

def _adversarial_attack_test(
    torch_model,
    X: np.ndarray,
    y_true: np.ndarray,
    eps: float = 0.05,
) -> Optional[Dict[str, float]]:
    if not _HAS_ATTACKS:
        return None
    try:
        import torch

        # Only run FGSM for true multiclass
        out0 = torch_model(torch.tensor(X[:1], dtype=torch.float32))
        if out0.ndim < 2 or out0.size(1) <= 1:
            return None

        # sample up to 100 for speed
        sample = X[:100]
        target = y_true[:100]
        atk = ta.FGSM(torch_model, eps=eps)
        adv = atk(
            torch.tensor(sample, dtype=torch.float32),
            torch.tensor(target, dtype=torch.long),
        )

        with torch.no_grad():
            out_clean = torch_model(torch.tensor(sample, dtype=torch.float32))
            out_adv = torch_model(adv)

        # Predictions
        if out_clean.ndim == 1 or (out_clean.ndim == 2 and out_clean.size(1) == 1):
            pred_clean = (out_clean.view(-1) > 0.5).long()
            pred_adv   = (out_adv.view(-1) > 0.5).long()
        else:
            pred_clean = out_clean.argmax(dim=1)
            pred_adv   = out_adv.argmax(dim=1)

        acc_clean = (pred_clean.cpu().numpy() == target).mean()
        acc_adv   = (pred_adv.cpu().numpy() == target).mean()
        return {
            "accuracy_clean": float(acc_clean),
            "accuracy_adv":   float(acc_adv),
            "delta_acc":      float(acc_clean - acc_adv),
        }
    except Exception:
        log.exception("Adversarial attack test failed")
        return None


def _basic_robustness(y_pred: np.ndarray) -> Dict[str, float]:
    return {"prediction_variance": float(np.var(y_pred))}


def analyze(
    y_pred: Union[np.ndarray, List[float]],
    y_true: Optional[Union[np.ndarray, List[float]]],
    X: pd.DataFrame,
    sensitive_attrs: List[str],
    model: Any | None = None,
    ref_stats_path: Union[str, Path, None] = None,
) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    y_pred_arr = np.asarray(y_pred)

    # Clustering
    if y_true is None:
        X_eval = X if len(X) <= 10_000 else X.sample(n=10_000, random_state=0)
        try:
            sil = silhouette_score(X_eval, y_pred_arr.astype(int))
            results["clustering"] = {"silhouette": float(sil)}
        except Exception:
            log.exception("Silhouette computation failed")
            results["clustering_error"] = "silhouette_failed"
        return results

    # Supervised
    y_true_arr = np.asarray(y_true).ravel()
    unique = np.unique(y_true_arr)
    is_binary = set(unique) <= {0, 1}
    is_reg = np.issubdtype(y_true_arr.dtype, np.floating)

    if is_binary:
        y_prob = np.clip(y_pred_arr.ravel(), 0, 1)
        y_bin = (y_prob >= 0.5).astype(int)
        results["performance"] = _compute_classification_performance(y_true_arr, y_prob, y_bin)
        results["performance_by_group"] = _performance_by_group(y_true_arr, y_bin, X, sensitive_attrs)

        fairness = {}
        for attr in sensitive_attrs:
            fm = _fairness_for_attr(attr, X, y_true_arr, y_bin)
            if _HAS_FAIRLEARN:
                try:
                    sf = X[attr].values
                    fm["demographic_parity_diff_fairlearn"] = float(
                        demographic_parity_difference(y_true_arr, y_bin, sensitive_features=sf)
                    )
                    fm["equalized_odds_diff_fairlearn"] = float(
                        equalized_odds_difference(y_true_arr, y_bin, sensitive_features=sf)
                    )
                except Exception:
                    log.exception("Fairlearn metrics failed")
            fairness[attr] = fm
        results["fairness"] = fairness

        if len(sensitive_attrs) >= 2:
            results["fairness_intersectional"] = _fairness_intersectional(sensitive_attrs, X, y_true_arr, y_bin)

    elif is_reg:
        results["performance"] = _compute_regression_performance(y_true_arr, y_pred_arr)

    else:
        n_classes = len(unique)
        if y_pred_arr.ndim != 2 or y_pred_arr.shape[1] != n_classes:
            raise ValueError("Pour le multiclasses, y_pred doit être un array (N,K) de probas")
        y_prob = np.clip(y_pred_arr, 0, 1)
        y_lab = y_prob.argmax(axis=1)
        results["performance"] = _compute_classification_performance(y_true_arr, y_prob, y_lab)
        results["performance_by_group"] = _performance_by_group(y_true_arr, y_lab, X, sensitive_attrs)

    if model is not None:
        shap_imp = _shap_global_importance(model, X)
        if shap_imp:
            results["explainability"] = {"mean_abs_shap_values": shap_imp}

    if ref_stats_path:
        drift = _compute_drift(X, ref_stats_path)
        if drift:
            results["drift"] = drift

    robust = _basic_robustness(y_pred_arr)
    if model is not None:
        adv = _adversarial_attack_test(model, X.values, np.asarray(y_true).ravel())
        if adv:
            robust["adversarial"] = adv
    results["robustness"] = robust

    return results
