import cv2
import json
import glob
import os
import re
import numpy as np
from scoreboard_cv import (
    is_scoreboard_visible,
    preprocess_pipeline_clahe,
    ScoreboardOCRProcessor,
    map_to_player_rows,
    extract_header_name,
    detect_active_highlight_row
)

video_path = "bowling_scoreboard.mp4"
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
sample_step = max(1, int(round(fps / 5.0)))

ocr_processor = ScoreboardOCRProcessor(engine_name="paddleocr")
roi_coords = (10, 850, 70, 1890)
ymin, ymax, xmin, xmax = roi_coords

frame_idx = 0
results = []
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    if frame_idx % sample_step == 0:
        ts = round(frame_idx / fps, 2)
        if is_scoreboard_visible(frame, roi_coords):
            crop_bgr = frame[ymin:ymax, xmin:xmax]
            active_row = detect_active_highlight_row(crop_bgr)
            prep_img = preprocess_pipeline_clahe(crop_bgr, scale=1.0)
            prep_path = f"debug/scratch_test_{ts:.1f}s.png"
            cv2.imwrite(prep_path, prep_img)
            dets = ocr_processor.run_ocr(prep_path)
            if os.path.exists(prep_path):
                os.remove(prep_path)
            hdr = extract_header_name(dets)
            results.append({
                "ts": ts,
                "active_row": active_row,
                "header_name": hdr,
                "dets": dets
            })
            if active_row or hdr:
                print(f"[{ts:5.1f}s] Active Row: {active_row}, Header Name: {hdr}")
    frame_idx += 1
cap.release()

with open("debug/scratch_ocr_dump.json", "w") as f:
    json.dump(results, f, indent=2)
print("Dump completed.")
