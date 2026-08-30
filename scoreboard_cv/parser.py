import re
import cv2
import numpy as np

def map_to_player_rows(detections: list, img_height: int = 840, img_width: int = 1820) -> list:
    """
    Maps 2D OCR detections into 3 horizontal player rows and 10 frame columns + TTL
    using exact spatial bounding box center coordinates.
    - Row 1: JAGDISH (Y in [135, 290)) -> Rolls: [135, 210), Cum: [210, 290)
    - Row 2: VISHAL  (Y in [290, 460)) -> Rolls: [290, 375), Cum: [375, 460)
    - Row 3: TARUN   (Y in [460, 640)) -> Rolls: [460, 550), Cum: [550, 640)
    - Columns: F1..F10, TTL
    """
    col_bounds = {
        "NAME": (0, 200), "F1": (200, 340), "F2": (340, 480), "F3": (480, 620),
        "F4": (620, 760), "F5": (760, 900), "F6": (900, 1040), "F7": (1040, 1180),
        "F8": (1180, 1320), "F9": (1320, 1460), "F10": (1460, 1630), "TTL": (1630, 1820)
    }
    player_names = {1: "JAGDISH", 2: "VISHAL", 3: "TARUN"}

    rows = []
    for r_idx in [1, 2, 3]:
        p_name = player_names[r_idx]
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
    footer_y_limit = 640

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

        # Assign Player Row strictly by vertical position
        if center_y < 290:
            r_idx = 0
            split_y = 210
        elif center_y < 460:
            r_idx = 1
            split_y = 375
        else:
            r_idx = 2
            split_y = 550

        r_dict = rows[r_idx]
        r_dict["raw_items"].append(det)

        # Assign Column strictly by horizontal position
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
