import torch.nn as nn

class MyModel(nn.Module):
    """Flexible output_dim: 1 pour régression/binaire,
       ou n_classes pour multiclass."""
    def __init__(self, input_dim: int, hidden: int = 32, output_dim: int = 1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, output_dim),
        )

    def forward(self, x):
        return self.net(x)
