# app/routers/templates.py
from datetime import datetime
from io import BytesIO
from pathlib import Path
import zipfile

from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse

from app.auth import get_current_user, User

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/model", summary="Télécharge le template de projet modèle")
def download_model_template(_: User = Depends(get_current_user)):
    """
    Génére un zip en mémoire :
    .
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
        headers={
            "Content-Disposition": 'attachment; filename="model_template.zip"'
        },
    )


# ────────────────────────── Contenu des fichiers ────────────────────────────
MODEL_PY = """\
import torch.nn as nn


class MyModel(nn.Module):
    \"\"\"Exemple minimal – à modifier !\"\"\"

    def __init__(self, input_dim: int, hidden: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, 1),
        )

    def forward(self, x):
        return self.net(x)
"""

TRAIN_PY = """\
import argparse, yaml, pandas as pd, torch
from pathlib import Path
from model import MyModel


def train_and_save_model(data_path: Path, config_path: Path, output_dir: Path):
    cfg = yaml.safe_load(open(config_path))
    df = pd.read_csv(data_path)
    X = torch.tensor(df.drop(cfg["target"], axis=1).values, dtype=torch.float32)
    y = torch.tensor(df[cfg["target"]].values, dtype=torch.float32).view(-1, 1)

    model = MyModel(input_dim=X.shape[1], hidden=cfg["hidden"])
    optim = torch.optim.Adam(model.parameters(), lr=cfg["lr"])
    loss_fn = torch.nn.MSELoss()

    for epoch in range(cfg["epochs"]):
        pred = model(X)
        loss = loss_fn(pred, y)
        optim.zero_grad()
        loss.backward()
        optim.step()
        if epoch % 10 == 0:
            print(f"epoch={epoch} loss={loss.item():.4f}")

    output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output_dir / "model.pt")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data")
    p.add_argument("--config")
    p.add_argument("--out")
    args = p.parse_args()
    train_and_save_model(Path(args.data), Path(args.config), Path(args.out))
"""

CONFIG_YAML = """\
# Hyper-paramètres modifiables dans l’UI
target: target_column_name
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
# Template de projet IA ({date})

## Contrat d’intégration

* `train.py` **doit** exposer `train_and_save_model(data_path, config_path, output_dir)`
* Le modèle doit être sauvegardé dans `output_dir` (format libre : `model.pt`, `model.joblib`, …)
* Les dépendances Python vont dans `requirements.txt`
"""
