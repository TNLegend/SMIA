import argparse
import logging
import yaml
import pandas as pd
import torch
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
    else:
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
        output_dim = 1  # Pour classification binaire, on veut output_dim=1
        model = MyModel(input_dim=X.shape[1], hidden=cfg["hidden"], output_dim=output_dim)
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
