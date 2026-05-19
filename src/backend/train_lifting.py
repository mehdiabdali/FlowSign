import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import Dataset, DataLoader

# ── Même architecture que définie précédemment ────────────────────────────────
class ResidualBlock(nn.Module):
    def __init__(self, size=1024, dropout=0.5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(size, size), nn.BatchNorm1d(size),
            nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(size, size), nn.BatchNorm1d(size),
            nn.ReLU(), nn.Dropout(dropout),
        )
    def forward(self, x):
        return x + self.net(x)

class Lifting2Dto3D(nn.Module):
    def __init__(self, n_joints=17, hidden=1024, dropout=0.5):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(n_joints * 2, hidden), nn.BatchNorm1d(hidden),
            nn.ReLU(), nn.Dropout(dropout),
        )
        self.res1 = ResidualBlock(hidden, dropout)
        self.res2 = ResidualBlock(hidden, dropout)
        self.head = nn.Linear(hidden, n_joints * 3)

    def forward(self, x):
        return self.head(self.res2(self.res1(self.encoder(x))))


# Adapter H36MDataset pour le format VideoPose3D
class H36MDataset(Dataset):
    def __init__(self, npz_path):
        data    = np.load(npz_path, allow_pickle=True)
        # VideoPose3D stocke les données par sujet/action dans un dict
        all_2d, all_3d = [], []

        for subject in data['positions_2d'].item().values():
            for action in subject.values():
                all_2d.append(action)   # (T, 17, 2)

        for subject in data['positions_3d'].item().values():
            for action in subject.values():
                all_3d.append(action)   # (T, 17, 3)

        pose_2d = np.concatenate(all_2d, axis=0).astype(np.float32)
        pose_3d = np.concatenate(all_3d, axis=0).astype(np.float32)
        pose_3d -= pose_3d[:, 0:1, :]   # centrer sur le pelvis

        self.pose_2d = torch.tensor(pose_2d.reshape(-1, 34))
        self.pose_3d = torch.tensor(pose_3d.reshape(-1, 51))

    def __len__(self):  return len(self.pose_2d)
    def __getitem__(self, i): return self.pose_2d[i], self.pose_3d[i]


# ── Boucle d'entraînement ─────────────────────────────────────────────────────
def train(npz_path, epochs=50, batch_size=1024, lr=1e-3):
    dataset    = H36MDataset(npz_path)
    loader     = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    model      = Lifting2Dto3D(n_joints=17)
    optimizer  = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler  = torch.optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)
    criterion  = nn.MSELoss()

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for p2d, p3d in loader:
            optimizer.zero_grad()
            pred  = model(p2d)
            loss  = criterion(pred, p3d)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        scheduler.step()
        print(f"Epoch {epoch+1}/{epochs} — loss: {total_loss/len(loader):.2f}")

    torch.save(model.state_dict(), "lifting_h36m.pth")
    print("Modèle sauvegardé : lifting_h36m.pth")
    return model

train("data_2d_h36m_gt.npz")