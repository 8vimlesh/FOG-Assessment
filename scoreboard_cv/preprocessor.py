import cv2
import numpy as np

def preprocess_pipeline_clahe(crop_bgr: np.ndarray, scale: float = 1.0) -> np.ndarray:
    """
    Computer Vision Preprocessing Pipeline:
    1. Upscale (if scale != 1.0)
    2. High-Contrast Grayscale conversion
    3. Contrast Limited Adaptive Histogram Equalization (CLAHE)
    4. Bilateral Edge-Preserving Denoising
    """
    h, w = crop_bgr.shape[:2]
    if scale != 1.0:
        upscaled = cv2.resize(crop_bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
    else:
        upscaled = crop_bgr
    
    gray = cv2.cvtColor(upscaled, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    denoised = cv2.bilateralFilter(enhanced, d=5, sigmaColor=50, sigmaSpace=50)
    return denoised
