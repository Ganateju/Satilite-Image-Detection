import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from torchvision.models import ResNet18_Weights
import numpy as np


class SiameseChangeDetector(nn.Module):
    """Zero-shot change detector using a frozen pretrained ResNet-18 backbone."""

    def __init__(self):
        super().__init__()
        resnet = models.resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
        self.feature_extractor = nn.Sequential(*list(resnet.children())[:-2])
        self.eval()

    def forward(self, img1, img2):
        with torch.no_grad():
            feat1 = self.feature_extractor(img1)
            feat2 = self.feature_extractor(img2)
            diff  = torch.abs(feat1 - feat2)
            cmap  = torch.mean(diff, dim=1, keepdim=True)
            cmap  = nn.functional.interpolate(
                cmap, size=(img1.shape[2], img1.shape[3]),
                mode="bilinear", align_corners=False,
            )
            bs   = cmap.shape[0]
            flat = cmap.view(bs, -1)
            vmin = flat.min(dim=1, keepdim=True)[0]
            vmax = flat.max(dim=1, keepdim=True)[0]
            flat = (flat - vmin) / (vmax - vmin + 1e-8)
            flat = flat ** 2
            cmap = flat.view(bs, 1, img1.shape[2], img1.shape[3])
        return cmap


def build_model() -> SiameseChangeDetector:
    """Instantiate and return the model. Call once and cache the result."""
    return SiameseChangeDetector()


_normalize = transforms.Normalize(
    mean=[0.485, 0.456, 0.406],
    std=[0.229, 0.224, 0.225],
)


def detect_changes_zero_shot(img1_np: np.ndarray, img2_np: np.ndarray,
                              threshold: float = 0.15,
                              model: SiameseChangeDetector | None = None):
    """
    Run zero-shot change detection.

    Parameters
    ----------
    img1_np, img2_np : np.ndarray  shape (H, W, 3), dtype uint8 (0-255)
    threshold        : float       binarisation threshold
    model            : pre-built SiameseChangeDetector (pass cached instance)

    Returns
    -------
    (binary_mask: np.ndarray bool, change_map_np: np.ndarray float32)
    """
    if model is None:
        model = build_model()

    t1 = _normalize(
        torch.from_numpy(img1_np).permute(2, 0, 1).unsqueeze(0).float() / 255.0
    )
    t2 = _normalize(
        torch.from_numpy(img2_np).permute(2, 0, 1).unsqueeze(0).float() / 255.0
    )
    cmap = model(t1, t2)
    cmap_np = cmap.squeeze().numpy()
    return cmap_np > threshold, cmap_np
