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
