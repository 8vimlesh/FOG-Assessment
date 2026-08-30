import cv2
import numpy as np

def is_scoreboard_visible(frame_bgr: np.ndarray, roi_coords: tuple = (10, 850, 70, 1890)) -> bool:
    """
    Detects whether the overhead bowling scoreboard grid is visible in the frame.
    Returns True for scoreboard frames and False for camera cutaways (e.g. lane/pin view).
    
    Robust classification features:
    1. Grid Edge Density: Digital scoreboard grid lines and text produce high edge gradient density (> 0.028).
    2. Header Luminance: Overhead scoreboard top header region has controlled luminance (70 to 130).
       Camera lane/pin cutaways have either dark bottom lane or overexposed ceiling lighting.
    """
    ymin, ymax, xmin, xmax = roi_coords
    roi = frame_bgr[ymin:ymax, xmin:xmax]
    if roi is None or roi.size == 0:
        return False

    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Check top header region inside ROI [y: 30-130, x: 1500-1800]
    hdr = gray_roi[30:130, 1500:1800]
    if hdr.size == 0:
        return False
    hdr_mean = float(np.mean(hdr))

    # Canny edge density across the scoreboard ROI
    edges = cv2.Canny(gray_roi, 50, 150)
    edge_density = float(np.mean(edges > 0))

    # Scoreboard frames have prominent grid lines (edge_density > 0.028) and moderate header mean (70..130)
    is_vis = (edge_density > 0.028) and (70.0 <= hdr_mean <= 130.0)
    return bool(is_vis)

def extract_scoreboard_roi(frame_bgr: np.ndarray, roi_coords: tuple = (10, 850, 70, 1890)) -> np.ndarray:
    """
    Extracts the cropped scoreboard ROI from a full 1080p frame.
    """
    ymin, ymax, xmin, xmax = roi_coords
    return frame_bgr[ymin:ymax, xmin:xmax]
