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

# ─────────────────────────── Dépendances Optionnelles ────────────────────────────
# BLOC DE GESTION DES DÉPENDANCES OPTIONNELLES
# Cette section tente d'importer des bibliothèques spécialisées (SHAP, Alibi Detect,
# Fairlearn, etc.). L'utilisation de blocs `try...except ImportError` permet au
# système de fonctionner même si ces librairies ne sont pas installées.
# Des variables booléennes (ex: `_HAS_SHAP`) sont utilisées comme des "drapeaux"
# pour activer ou désactiver les fonctionnalités correspondantes dans le reste du code.
# C'est une excellente pratique pour rendre une application modulaire et flexible.

try:
    import shap  # Pour l'explicabilité des modèles
    _HAS_SHAP = True
except ImportError:
    _HAS_SHAP = False
    shap = None

try:
    from alibi_detect.cd import KSDrift  # Pour la détection de "data drift"
    _HAS_ALIBI = True
except ImportError:
    _HAS_ALIBI = False
    KSDrift = None

try:
    import torchattacks as ta  # Pour simuler des attaques adverses (robustesse)
    _HAS_ATTACKS = True
except ImportError:
    _HAS_ATTACKS = False
    ta = None

try:
    # Pour le calcul des métriques d'équité (fairness)
    from fairlearn.metrics import (
        demographic_parity_difference,
        equalized_odds_difference,
    )
    _HAS_FAIRLEARN = True
except ImportError:
    _HAS_FAIRLEARN = False

try:
    # Pour la génération de rapports de data drift
    from evidently.profile import Profile
    from evidently.profile.sections import DataDriftProfileSection
    from evidently.dashboard import Dashboard
    from evidently.dashboard.tabs import DataDriftTab
    _HAS_EVIDENTLY = True
except ImportError:
    _HAS_EVIDENTLY = False


# ─────────────────────────── Fonctions de Métriques ────────────────────────────

def _compute_classification_performance(
    y_true: np.ndarray, y_prob: np.ndarray, y_pred: np.ndarray
) -> Dict[str, float]:
    # BLOC DE CALCUL DES MÉTRIQUES DE PERFORMANCE - CLASSIFICATION
    # Cette fonction calcule un dictionnaire de métriques de performance standard
    # pour les tâches de classification.
    # Elle s'adapte automatiquement au cas binaire (ex: `precision`, `recall`) ou
    # multi-classe (ex: `precision_macro`, `auc_ovr` pour One-vs-Rest).
    unique_classes = np.unique(y_true)
    if set(unique_classes) <= {0, 1}:  # Cas binaire
        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1": float(f1_score(y_true, y_pred, zero_division=0)),
            "auc": float(roc_auc_score(y_true, y_prob)),
            "mse": float(mean_squared_error(y_true, y_prob)),
        }
    else:  # Cas multi-classe
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
    # BLOC DE CALCUL DES MÉTRIQUES DE PERFORMANCE - RÉGRESSION
    # Fonction dédiée au calcul des métriques de performance standard
    # pour les tâches de régression : erreur quadratique moyenne (MSE),
    # erreur absolue moyenne (MAE) et le coefficient de détermination (R²).
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
    # BLOC D'ANALYSE DE PERFORMANCE PAR SOUS-GROUPE (BIAIS)
    # Cette fonction est essentielle pour l'analyse de l'équité (fairness).
    # Elle calcule les métriques de performance (accuracy, f1) pour chaque
    # sous-groupe d'une population, défini par les colonnes dans `group_cols`.
    # Par exemple, si `group_cols` contient "sexe", elle calculera les métriques
    # séparément pour les hommes et les femmes. Le résultat permet de détecter
    # des disparités de performance entre les groupes.
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
                "support": int(mask.sum()),  # Taille du groupe
                "accuracy": float(accuracy_score(y_true[mask], y_pred[mask])),
                "f1": float(f1_score(y_true[mask], y_pred[mask], average=avg, zero_division=0)),
            }
    return out


def _parity_metrics(
    y_pred: np.ndarray, group: np.ndarray
) -> Tuple[float, float]:
    # BLOC DE CALCUL DES MÉTRIQUES DE PARITÉ (FAIRNESS)
    # Cette fonction calcule deux métriques fondamentales de l'équité statistique
    # pour un groupe binaire (ex: privilégié vs non-privilégié).
    # - `spd` (Statistical Parity Difference) : La différence des taux de prédictions
    #   positives entre les deux groupes. Proche de 0 = équitable.
    # - `di` (Disparate Impact) : Le ratio des taux de prédictions positives.
    #   Proche de 1 = équitable.
    pr_1 = y_pred[group == 1].mean()  # Taux de prédiction positive pour le groupe 1
    pr_0 = y_pred[group == 0].mean()  # Taux de prédiction positive pour le groupe 0
    spd = pr_1 - pr_0
    di = float(pr_1 / pr_0) if pr_0 else np.nan
    return spd, di

# ─────────────────────────── Fonctions de Métriques d'Équité (Fairness) ────────────────────────────

def _equal_opportunity(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    group: np.ndarray,
) -> float:
    # BLOC DE CALCUL DE L'ÉGALITÉ DES CHANCES (EQUAL OPPORTUNITY)
    # Cette métrique d'équité mesure la différence de "Taux de Vrais Positifs"
    # (rappel ou "recall") entre deux groupes. Un score proche de zéro indique
    # que le modèle identifie correctement les cas positifs avec la même
    # efficacité pour les deux groupes.
    mask1, mask0 = group == 1, group == 0
    tpr1 = recall_score(y_true[mask1], y_pred[mask1], zero_division=0)
    tpr0 = recall_score(y_true[mask0], y_pred[mask0], zero_division=0)
    return tpr1 - tpr0


def _predictive_parity(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    group: np.ndarray,
) -> float:
    # BLOC DE CALCUL DE LA PARITÉ PRÉDICTIVE (PREDICTIVE PARITY)
    # Cette métrique mesure la différence de "Valeur Prédictive Positive"
    # (précision ou "precision") entre deux groupes. Un score proche de zéro
    # indique que lorsque le modèle prédit un résultat positif, la probabilité
    # que ce soit correct est la même pour les deux groupes.
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
    # BLOC DE SYNTHÈSE DES MÉTRIQUES D'ÉQUITÉ POUR UN ATTRIBUT
    # Cette fonction orchestre le calcul d'un ensemble complet de métriques
    # d'équité pour un attribut sensible donné (ex: 'sexe', 'âge').
    # Elle crée d'abord un groupe binaire à partir de l'attribut :
    # - Si l'attribut est catégoriel, elle oppose la première catégorie aux autres.
    # - Si l'attribut est numérique, elle le sépare par rapport à sa médiane.
    # Ensuite, elle utilise les helpers précédents pour retourner un dictionnaire
    # complet des scores d'équité.
    if attr not in X.columns:
        return {"error": "column missing"}
    series = X[attr]
    if series.dtype.kind in "O":  # 'O' pour Object, typiquement les chaînes de caractères
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
    # BLOC D'ANALYSE D'ÉQUITÉ INTERSECTIONNELLE
    # Cette fonction pousse l'analyse plus loin en examinant les biais aux
    # intersections de plusieurs attributs (ex: "femme" ET "jeune").
    # Elle crée des sous-groupes en combinant les valeurs de paires d'attributs
    # et calcule pour chacun la performance de base (accuracy, taux de prédiction positive),
    # ce qui permet de déceler des biais qui n'apparaissent pas lorsqu'on
    # analyse les attributs de manière isolée.
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

# ─────────────────────────── Explicabilité du Modèle (SHAP) ────────────────────────────

def _shap_global_importance(model, X: pd.DataFrame, nsample: int = 500):
    # BLOC DE CALCUL DE L'IMPORTANCE GLOBALE DES FEATURES AVEC SHAP
    # Cette fonction utilise la bibliothèque SHAP pour "expliquer" le modèle,
    # en calculant l'importance de chaque feature sur les prédictions.
    # Elle fonctionne uniquement si SHAP est installé (`_HAS_SHAP`).
    # 1. Elle crée une fonction "wrapper" `predict_np` pour que SHAP, qui attend
    #    des `numpy.ndarray`, puisse communiquer avec le modèle (probablement PyTorch).
    # 2. Elle utilise un `KernelExplainer`, une méthode agnostique qui traite
    #    le modèle comme une boîte noire.
    # 3. Elle calcule les valeurs de SHAP sur un échantillon de données.
    # 4. Elle retourne l'importance globale de chaque feature (la moyenne des
    #    valeurs absolues de SHAP).
    if not _HAS_SHAP:
        return None
    try:
        import shap
        import torch

        def predict_np(x: np.ndarray) -> np.ndarray:
            with torch.no_grad():
                t = torch.tensor(x, dtype=torch.float32)
                out = model(t).cpu().numpy()
            if out.ndim == 1 or (out.ndim == 2 and out.shape[1] == 1):
                return out.reshape(-1)
            return out

        bg = shap.sample(X.values, min(100, len(X)), random_state=0)
        explainer = shap.KernelExplainer(predict_np, bg)
        subset = X.sample(n=min(nsample, len(X)), random_state=0).values
        shap_vals = explainer.shap_values(subset, nsample=nsample)

        if isinstance(shap_vals, list):
            abs_mean = np.mean([np.abs(arr).mean(axis=0) for arr in shap_vals], axis=0)
        else:
            abs_mean = np.abs(shap_vals).mean(axis=0)

        return dict(zip(X.columns, abs_mean.tolist()))
    except Exception:
        log.exception("SHAP explanation failed")
        return None

# ─────────────────────────── Détection de Dérive des Données (Data Drift) ────────────────────────

def _compute_psi(hist_ref: np.ndarray, hist_new: np.ndarray, epsilon: float = 1e-6) -> float:
    # Helper pour calculer le "Population Stability Index" (PSI), une métrique
    # qui quantifie le changement de distribution d'une variable entre deux datasets.
    hr = hist_ref + epsilon
    hn = hist_new + epsilon
    hr = hr / hr.sum()
    hn = hn / hn.sum()
    return float(np.sum((hn - hr) * np.log(hn / hr)))


def _compute_drift(
    X_test: pd.DataFrame,
    ref_stats_path: Union[str, Path],
) -> Optional[Dict[str, Any]]:
    # BLOC D'ANALYSE DE LA DÉRIVE DES DONNÉES
    # Cette fonction majeure compare un nouveau jeu de données (`X_test`) à un
    # jeu de données de référence pour détecter des changements de distribution ("drift").
    # Elle combine plusieurs techniques, si les bibliothèques sont disponibles :
    # 1. PSI : Calcule le "Population Stability Index" pour chaque feature numérique.
    # 2. Test KS (via Alibi Detect) : Applique un test statistique de Kolmogorov-Smirnov
    #    pour obtenir une p-value et déterminer si la dérive est statistiquement significative.
    # 3. Rapport Evidently : Génère un profil JSON et un rapport HTML très complets
    #    visualisant les dérives, offrant une analyse beaucoup plus détaillée.
    if not Path(ref_stats_path).exists():
        return None
    drift: Dict[str, Any] = {}
    ref_df = pd.read_csv(ref_stats_path)

    # 1) Calcul du PSI pour les colonnes numériques
    psi_vals = {}
    numeric_cols = X_test.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        hist_ref, bins = np.histogram(ref_df[col], bins=10, density=False)
        hist_new, _ = np.histogram(X_test[col], bins=bins, density=False)
        psi_vals[col] = _compute_psi(hist_ref, hist_new)
    drift["psi"] = psi_vals

    # 2) Test de dérive avec Alibi Detect (si installé)
    if _HAS_ALIBI:
        try:
            ref_vals = ref_df[numeric_cols].values
            scaler = StandardScaler().fit(ref_vals)
            ks = KSDrift(ref_vals, p_val=0.05, preprocess_fn=scaler.transform)
            preds = ks.predict(X_test[numeric_cols].values, drift_type="batch")
            p_arr = preds["data"]["p_val"]
            drift["ks_drift"] = {
                "is_drift": bool(preds["data"]["is_drift"]),
                "p_value": float(p_arr[0]) if hasattr(p_arr, "__len__") else float(p_arr),
            }
        except Exception:
            log.exception("KS drift test failed")

    # 3) Rapport de dérive avec Evidently (si installé)
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

# ─────────────────────────── Tests de Robustesse du Modèle ────────────────────────────

def _adversarial_attack_test(
    torch_model,
    X: np.ndarray,
    y_true: np.ndarray,
    eps: float = 0.05,
) -> Optional[Dict[str, float]]:
    # BLOC DE TEST DE ROBUSTESSE VIA ATTAQUE ADVERSE
    # Cette fonction évalue la robustesse d'un modèle en simulant une attaque
    # adverse simple : FGSM (Fast Gradient Sign Method). L'objectif est de voir
    # à quel point la performance du modèle chute lorsqu'on ajoute une petite
    # perturbation "intelligente" aux données d'entrée.
    # 1. Ne s'exécute que si `torchattacks` est installé et si le modèle est
    #    bien un classifieur multi-classe.
    # 2. Crée des exemples "adverses" (perturbés) à partir d'un échantillon.
    # 3. Compare l'accuracy du modèle sur les données propres et sur les données
    #    perturbées pour mesurer la dégradation de la performance.
    if not _HAS_ATTACKS:
        return None
    try:
        import torch

        out0 = torch_model(torch.tensor(X[:1], dtype=torch.float32))
        if out0.ndim < 2 or out0.size(1) <= 1:
            return None

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
    # Calcule la variance des prédictions, une heuristique très simple de la stabilité du modèle.
    return {"prediction_variance": float(np.var(y_pred))}


# ─────────────────────────── Fonction Principale d'Analyse ────────────────────────────

def analyze(
    y_pred: Union[np.ndarray, List[float]],
    y_true: Optional[Union[np.ndarray, List[float]]],
    X: pd.DataFrame,
    sensitive_attrs: List[str],
    model: Any | None = None,
    ref_stats_path: Union[str, Path, None] = None,
) -> Dict[str, Any]:
    # BLOC DE LA FONCTION D'ORCHESTRATION CENTRALE
    # C'est la fonction principale, le point d'entrée de ce module.
    # Elle prend en entrée les prédictions, les vraies valeurs, les données,
    # et optionnellement le modèle lui-même, puis génère un rapport d'analyse complet
    # en appelant toutes les fonctions `_helpers` définies plus haut.
    # Sa logique s'adapte en fonction du type de problème de Machine Learning détecté.
    results: Dict[str, Any] = {}
    y_pred_arr = np.asarray(y_pred)

    # Cas 1 : Problème non-supervisé (Clustering)
    # Si `y_true` n'est pas fourni, on suppose une tâche de clustering.
    if y_true is None:
        # Pour la performance, on échantillonne si le dataset est trop grand.
        X_eval = X if len(X) <= 10_000 else X.sample(n=10_000, random_state=0)
        try:
            # La métrique principale est le score de Silhouette.
            sil = silhouette_score(X_eval, y_pred_arr.astype(int))
            results["clustering"] = {"silhouette": float(sil)}
        except Exception:
            log.exception("Silhouette computation failed")
            results["clustering_error"] = "silhouette_failed"
        return results

    # Cas 2 : Problème supervisé
    y_true_arr = np.asarray(y_true).ravel()
    unique = np.unique(y_true_arr)
    is_binary = set(unique) <= {0, 1}
    is_reg = np.issubdtype(y_true_arr.dtype, np.floating)

    # Sous-cas : Classification Binaire
    if is_binary:
        y_prob = np.clip(y_pred_arr.ravel(), 0, 1)
        y_bin = (y_prob >= 0.5).astype(int)
        results["performance"] = _compute_classification_performance(y_true_arr, y_prob, y_bin)
        results["performance_by_group"] = _performance_by_group(y_true_arr, y_bin, X, sensitive_attrs)

        # Calcul des métriques d'équité (fairness)
        fairness = {}
        for attr in sensitive_attrs:
            fm = _fairness_for_attr(attr, X, y_true_arr, y_bin)
            # Enrichissement avec Fairlearn si disponible
            if _HAS_FAIRLEARN:
                try:
                    sf = X[attr].values
                    fm["demographic_parity_diff_fairlearn"] = float(demographic_parity_difference(y_true_arr, y_bin, sensitive_features=sf))
                    fm["equalized_odds_diff_fairlearn"] = float(equalized_odds_difference(y_true_arr, y_bin, sensitive_features=sf))
                except Exception:
                    log.exception("Fairlearn metrics failed")
            fairness[attr] = fm
        results["fairness"] = fairness
        # Calcul de l'équité intersectionnelle si pertinent
        if len(sensitive_attrs) >= 2:
            results["fairness_intersectional"] = _fairness_intersectional(sensitive_attrs, X, y_true_arr, y_bin)

    # Sous-cas : Régression
    elif is_reg:
        results["performance"] = _compute_regression_performance(y_true_arr, y_pred_arr)

    # Sous-cas : Classification Multi-classe
    else:
        n_classes = len(unique)
        if y_pred_arr.ndim != 2 or y_pred_arr.shape[1] != n_classes:
            raise ValueError("Pour le multiclasses, y_pred doit être un array (N,K) de probas")
        y_prob = np.clip(y_pred_arr, 0, 1)
        y_lab = y_prob.argmax(axis=1)
        results["performance"] = _compute_classification_performance(y_true_arr, y_prob, y_lab)
        results["performance_by_group"] = _performance_by_group(y_true_arr, y_lab, X, sensitive_attrs)

    # Analyses communes à tous les cas supervisés (si les dépendances sont fournies)
    # Explicabilité du modèle
    if model is not None:
        shap_imp = _shap_global_importance(model, X)
        if shap_imp:
            results["explainability"] = {"mean_abs_shap_values": shap_imp}

    # Détection de dérive des données
    if ref_stats_path:
        drift = _compute_drift(X, ref_stats_path)
        if drift:
            results["drift"] = drift

    # Robustesse du modèle
    robust = _basic_robustness(y_pred_arr)
    if model is not None:
        adv = _adversarial_attack_test(model, X.values, np.asarray(y_true).ravel())
        if adv:
            robust["adversarial"] = adv
    results["robustness"] = robust

    # Retourne le dictionnaire final contenant toutes les analyses
    return results