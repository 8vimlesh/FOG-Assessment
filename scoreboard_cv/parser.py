import re
import cv2
import numpy as np

def extract_header_name(detections: list) -> str:
    """
    Extracts the active bowler's full name from the header region:
    Y in [10, 100], X in [150, 600].
    """
    candidates = []
    for det in detections:
        bbox = det.get("bbox", [])
        if not bbox:
            continue
        cy = sum(p[1] for p in bbox) / len(bbox)
        cx = sum(p[0] for p in bbox) / len(bbox)
        text = det.get("text", "").strip().upper()
        if 10 <= cy <= 100 and 150 <= cx <= 600:
            cleaned = re.sub(r'[^A-Z]', '', text)
            if len(cleaned) >= 3 and cleaned not in ["TTL", "LANE", "FRAME"]:
                candidates.append((cleaned, det.get("confidence", 1.0)))
    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    return None

def detect_active_highlight_row(crop_bgr: np.ndarray) -> int:
    """
    Detects which player row (1..4) currently has the yellow active-bowler highlight.
    Indicator regions are on the left: X in [10, 120].
    Row 1: Y in [140, 280]
    Row 2: Y in [295, 435]
    Row 3: Y in [450, 590]
    Row 4: Y in [610, 750]
    Returns row index 1..4, or None if no active highlight detected.
    """
    if crop_bgr is None:
        return None
    row_y_ranges = [
        (1, 140, 280),
        (2, 295, 435),
        (3, 450, 590),
        (4, 610, 750)
    ]
    yellow_scores = []
    h, w = crop_bgr.shape[:2]
    for r_idx, y1, y2 in row_y_ranges:
        if y2 > h:
            continue
        patch = crop_bgr[y1:y2, 10:min(120, w)]
        b = patch[:, :, 0].astype(float)
        g = patch[:, :, 1].astype(float)
        r = patch[:, :, 2].astype(float)
        # Yellow metric: (R + G) / 2 - B (yellow has high R & G, low B; blue baseline has high B)
        yellow_metric = float(np.mean(((r + g) / 2.0) - b))
        yellow_scores.append((r_idx, yellow_metric))
    if not yellow_scores:
        return None
    best_row, best_score = max(yellow_scores, key=lambda x: x[1])
    if best_score > 50:
        return best_row
    return None

def map_to_player_rows(detections: list, img_height: int = 840, img_width: int = 1820, player_names: dict = None) -> list:
    """
    Maps 2D OCR detections into 4 horizontal player rows (Rows 1..4) and 10 frame columns + TTL
    using calibrated spatial bounding box center coordinates across the full 840px ROI.
    - Row 1: [135, 290) -> Rolls: [135, 205), Cum: [205, 290)
    - Row 2: [290, 460) -> Rolls: [290, 370), Cum: [370, 460)
    - Row 3: [460, 630) -> Rolls: [460, 535), Cum: [535, 630)
    - Row 4: [630, 830) -> Rolls: [630, 700), Cum: [700, 830)
    - Columns: F1..F10, TTL
    """
    col_bounds = {
        "NAME": (0, 200), "F1": (200, 340), "F2": (340, 480), "F3": (480, 620),
        "F4": (620, 760), "F5": (760, 900), "F6": (900, 1040), "F7": (1040, 1180),
        "F8": (1180, 1320), "F9": (1320, 1460), "F10": (1460, 1630), "TTL": (1630, 1820)
    }

    default_names = {1: "JAGDISH", 2: "VISHAL", 3: "P (Player 3)", 4: "TARUN"}
    names_map = player_names if player_names is not None else default_names

    rows = []
    for r_idx in [1, 2, 3, 4]:
        p_name = names_map.get(r_idx, f"UNKNOWN_ROW_{r_idx}")
        r_data = {
            "row_index": r_idx,
            "player_name": p_name,
            "name_confidence": 1.0,
            "frames": {f"F{f}": {"rolls": [], "cumulative": None, "raw_detections": []} for f in range(1, 11)},
            "ttl_value": "unknown",
            "ttl_confidence": 0.0,
            "raw_items": []
        }
        rows.append(r_data)

    header_y_limit = 135
    footer_y_limit = 830

    for det in detections:
        bbox = det["bbox"]
        ys = [p[1] for p in bbox]
        xs = [p[0] for p in bbox]
        x1, x2 = min(xs), max(xs)
        center_y = int(sum(ys) / len(ys))
        center_x = int(sum(xs) / len(xs))
        width = x2 - x1
        text = det["text"].strip()
        conf = det["confidence"]

        if center_y < header_y_limit or center_y >= footer_y_limit:
            continue

        # Assign Player Row strictly by calibrated vertical position
        if center_y < 290:
            r_idx = 0
            split_y = 205
        elif center_y < 460:
            r_idx = 1
            split_y = 370
        elif center_y < 630:
            r_idx = 2
            split_y = 535
        else:
            r_idx = 3
            split_y = 700

        r_dict = rows[r_idx]
        r_dict["raw_items"].append(det)

        # Assign Column strictly by calibrated horizontal position
        assigned_col = None
        for c_name, (c_x1, c_x2) in col_bounds.items():
            if c_x1 <= center_x < c_x2:
                assigned_col = c_name
                break
        if not assigned_col:
            assigned_col = "TTL" if center_x >= 1630 else "NAME"

        if assigned_col == "NAME":
            continue
        elif assigned_col == "TTL":
            digits = re.sub(r'[^0-9]', '', text)
            if digits and int(digits) > 0 and (r_dict["ttl_value"] == "unknown" or conf > r_dict["ttl_confidence"]):
                r_dict["ttl_value"] = digits
                r_dict["ttl_confidence"] = conf
        else:
            f_cell = r_dict["frames"][assigned_col]
            f_cell["raw_detections"].append(det)

            # Check if multi-column merged artifact
            is_merged = (width > 180) or bool(re.search(r'\d{3,}', text))
            is_roll = (center_y < split_y)

            if is_roll:
                if is_merged:
                    m = re.search(r'([0-9xX/\-]{1,2})', text)
                    if m:
                        f_cell["rolls"].append(m.group(1))
                    else:
                        f_cell["rolls"].append(f"unknown ({text})")
                else:
                    f_cell["rolls"].append(text)
            else:
                if is_merged:
                    m = re.search(r'(\d{1,3})', text)
                    if m:
                        f_cell["cumulative"] = m.group(1)
                    else:
                        f_cell["cumulative"] = f"unknown ({text})"
                else:
                    digits = re.sub(r'[^0-9]', '', text)
                    f_cell["cumulative"] = digits if digits else text

    return rows
