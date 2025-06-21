# app/routers/templates.py
from datetime import datetime
from io import BytesIO
from pathlib import Path
import zipfile

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.auth import get_current_user, User

router = APIRouter(prefix="/templates", tags=["templates"])

@router.get("/model", summary="Télécharge le template de projet modèle")
def download_model_template(_: User = Depends(get_current_user)):
    """
    Génère un zip en mémoire :
    ├── model.py
    ├── train.py
    ├── config.yaml
    ├── requirements.txt
    └── README.md
    """
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        now = datetime.utcnow().isoformat()
        files: dict[str, str] = {
            "model.py": MODEL_PY,
            "train.py": TRAIN_PY,
            "config.yaml": CONFIG_YAML,
            "requirements.txt": REQUIREMENTS_TXT,
            "README.md": README_MD.format(date=now),
        }
        for name, content in files.items():
            z.writestr(name, content)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="model_template.zip"'},
    )

# ────────────────────────── Contenu des fichiers ────────────────────────────
MODEL_PY = """\
import torch.nn as nn

class MyModel(nn.Module):
    \"\"\"Flexible output_dim: 1 pour régression/binaire,
       ou n_classes pour multiclass.\"\"\"
    def __init__(self, input_dim: int, hidden: int = 32, output_dim: int = 1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, output_dim),
        )

    def forward(self, x):
        return self.net(x)
"""

TRAIN_PY = """\
import argparse, logging, yaml, pandas as pd, torch
from pathlib import Path
from model import MyModel

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def train_and_save_model(data_path: Path, config_path: Path, output_dir: Path):
    cfg = yaml.safe_load(open(config_path, encoding="utf-8"))
    df = pd.read_csv(data_path)

    # Prépare X et y
    if cfg["task"] == "clustering":
        X_df, y = df, None
    else:
        X_df, y_series = df.drop(cfg["target"], axis=1), df[cfg["target"]]

    X = torch.tensor(X_df.values, dtype=torch.float32)

    # Classification → construction de y long + output_dim
    if cfg["task"] == "classification":
        classes = sorted(y_series.unique())
        n_classes = len(classes)
        y = torch.tensor(
            y_series.astype(pd.CategoricalDtype(categories=classes))
                    .cat.codes.values,
            dtype=torch.long
        )
        output_dim = n_classes
    elif cfg["task"] == "regression":
        y = torch.tensor(y_series.values, dtype=torch.float32).view(-1, 1)
        output_dim = 1
    else:  # clustering
        model = MyModel(input_dim=X.shape[1], hidden=cfg["hidden"], output_dim=1)
        with torch.no_grad():
            outs = model(X)
        output_dir.mkdir(exist_ok=True, parents=True)
        torch.save(outs.cpu(), output_dir / "cluster_outputs.pt")
        return

    model = MyModel(input_dim=X.shape[1], hidden=cfg["hidden"], output_dim=output_dim)

    # Choix de la loss
    if cfg["task"] == "classification" and n_classes > 2:
        loss_fn = torch.nn.CrossEntropyLoss()
    elif cfg["task"] == "classification":
        loss_fn = torch.nn.BCEWithLogitsLoss()
        y = y.float().view(-1, 1)
    else:
        loss_fn = torch.nn.MSELoss()

    optim = torch.optim.Adam(model.parameters(), lr=cfg["lr"])

    # Boucle d'entraînement
    for epoch in range(cfg["epochs"]):
        optim.zero_grad()
        logits = model(X)
        if isinstance(loss_fn, torch.nn.CrossEntropyLoss):
            loss = loss_fn(logits, y.view(-1))
        else:
            loss = loss_fn(logits, y)
        loss.backward()
        optim.step()
        if epoch % 10 == 0:
            log.info(f"epoch={epoch} loss={loss.item():.4f}")

    output_dir.mkdir(exist_ok=True, parents=True)
    torch.save(model.state_dict(), output_dir / "model.pt")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--config", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    train_and_save_model(Path(args.data), Path(args.config), Path(args.out))
"""

CONFIG_YAML = """\
## task: regression, classification ou clustering
task: classification
# si regression/classification :
target: votre_colonne_cible
hidden: 32
lr: 0.001
epochs: 50
"""

REQUIREMENTS_TXT = """\
torch>=2.2
pandas
pyyaml
"""

README_MD = """\
# Template IA ({date})

## Contrat d’intégration

* `train.py` doit exposer `train_and_save_model(data_path, config_path, output_dir)`
* En classification, on supporte binaire et multiclass
* Le modèle (state_dict) est sauvegardé dans `model.pt`
* Pour le clustering, on sauvegarde dans `cluster_outputs.pt`
* Les dépendances vont dans `requirements.txt`
"""
