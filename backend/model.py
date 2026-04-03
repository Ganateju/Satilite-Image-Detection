import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
import numpy as np

class SiameseChangeDetector(nn.Module):
    def __init__(self):
        super(SiameseChangeDetector, self).__init__()
        # Use a pre-trained ResNet as a feature extractor
        resnet = models.resnet18(pretrained=True)
        # Remove the classification head (fc and avgpool)
        self.feature_extractor = nn.Sequential(*list(resnet.children())[:-2])
        self.eval() # Always in eval mode for zero-shot
    
    def forward(self, img1, img2):
        # img1, img2: [B, C, H, W] normalized RGB images.
        with torch.no_grad():
            feat1 = self.feature_extractor(img1)
            feat2 = self.feature_extractor(img2)
            
            # Simple absolute difference in feature space
            diff = torch.abs(feat1 - feat2)
            
            # Aggregate across channel dimensions to get a single activation map
            # [B, C, H', W'] -> [B, 1, H', W']
            change_map = torch.mean(diff, dim=1, keepdim=True)
            
            # Upsample it back to original image size
            change_map = nn.functional.interpolate(
                change_map, size=(img1.shape[2], img1.shape[3]), mode='bilinear', align_corners=False
            )
            
            # Min-max normalize the change map for thresholding
            batch_size = change_map.shape[0]
            change_map = change_map.view(batch_size, -1)
            c_min = change_map.min(dim=1, keepdim=True)[0]
            c_max = change_map.max(dim=1, keepdim=True)[0]
            change_map = (change_map - c_min) / (c_max - c_min + 1e-8)
            
            # Additional contrast stretch for better thresholding via exponentiation
            change_map = change_map ** 2
            
            change_map = change_map.view(batch_size, 1, img1.shape[2], img1.shape[3])
            
        return change_map

def detect_changes_zero_shot(img1_np, img2_np, threshold=0.15):
    """
    img1_np, img2_np: numpy arrays of shape (H, W, 3), range 0-255.
    Returns: binary numpy mask (H, W)
    """
    model = SiameseChangeDetector()
    
    # Convert to torch tensors
    t1 = torch.from_numpy(img1_np).permute(2, 0, 1).unsqueeze(0).float() / 255.0
    t2 = torch.from_numpy(img2_np).permute(2, 0, 1).unsqueeze(0).float() / 255.0
    
    # Standard imagenet normalization
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    t1 = normalize(t1)
    t2 = normalize(t2)
    change_map = model(t1, t2)
    change_map_np = change_map.squeeze().numpy()
    
    # Thresholding
    binary_mask = (change_map_np > threshold)
    return binary_mask, change_map_np
