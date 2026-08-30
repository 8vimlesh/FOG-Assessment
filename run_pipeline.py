import argparse
import cv2
import json
import csv
import os
import glob
import time
import numpy as np

from scoreboard_cv import (
    is_scoreboard_visible,
    preprocess_pipeline_clahe,
    ScoreboardOCRProcessor,
    map_to_player_rows,
    ScoreboardTemporalAggregator,
)

def main():
    parser = argparse.ArgumentParser(description="Bowling Scoreboard Computer Vision Extraction Pipeline")
    parser.add_argument("--video", type=str, default="bowling_scoreboard.mp4", help="Path to input bowling scoreboard video file")
    parser.add_argument("--output_dir", type=str, default="output", help="Directory to save final output JSON & CSV files")
    parser.add_argument("--debug_dir", type=str, default="debug", help="Directory to save debug crops and reports")
    args = parser.parse_args()

    video_path = args.video
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at '{video_path}'")
        return

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.debug_dir, exist_ok=True)

    print("=" * 70)
    print("BOWLING SCOREBOARD COMPUTER VISION EXTRACTION PIPELINE")
    print(f"Processing Video: {video_path}")
    print("=" * 70)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0.0
    cap.release()

    print(f"[1/5] Video Loaded: {fps:.2f} FPS | {total_frames} Frames | {duration:.2f}s Duration")

    ocr_processor = ScoreboardOCRProcessor(engine_name="paddleocr")
    aggregator = ScoreboardTemporalAggregator(window_size=5, min_confidence=0.50)

    # Sample approximately 5 FPS across the video (every 6th frame @ 30 FPS)
    sample_step = max(1, int(round(fps / 5.0)))
    total_sampled_frames = (total_frames + sample_step - 1) // sample_step

    print(f"\n[2/5] Running Temporal Sampling ({total_sampled_frames} frames @ ~5 FPS), Cutaway Detection & PaddleOCR...", flush=True)
    cap = cv2.VideoCapture(video_path)
    roi_coords = (10, 850, 70, 1890)
    ymin, ymax, xmin, xmax = roi_coords

    last_ocr_crop = None
    last_ocr_data = None
    last_player_state_summary = {}

    frame_idx = 0
    obs_idx = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % sample_step == 0:
            obs_idx += 1
            actual_ts = round(frame_idx / fps, 2)
            is_visible = is_scoreboard_visible(frame, roi_coords)

            if not is_visible:
                last_ocr_crop = None
                last_ocr_data = None
                ocr_data = {
                    "timestamp": actual_ts,
                    "filename": f"frame_{actual_ts:05.1f}s.png",
                    "detections": [],
                    "player_rows": []
                }
                aggregator.process_frame(timestamp=actual_ts, raw_ocr_data=ocr_data)
                print(f"[{actual_ts:5.1f}s]\nHIDDEN/CUTAWAY", flush=True)
            else:
                crop_bgr = frame[ymin:ymax, xmin:xmax]
                need_ocr = True
                if last_ocr_crop is not None and last_ocr_data is not None:
                    diff = float(np.mean(cv2.absdiff(crop_bgr, last_ocr_crop)))
                    if diff < 4.0:
                        need_ocr = False

                if need_ocr:
                    prep_img = preprocess_pipeline_clahe(crop_bgr, scale=1.0)
                    prep_path = os.path.join(args.debug_dir, "preprocessed", f"prep_frame_{actual_ts:04.1f}s.png")
                    os.makedirs(os.path.dirname(prep_path), exist_ok=True)
                    cv2.imwrite(prep_path, prep_img)

                    raw_ocr = ocr_processor.run_ocr(prep_path)
                    if len(raw_ocr) < 15:
                        is_visible = False
                        ocr_data = {
                            "timestamp": actual_ts,
                            "filename": f"frame_{actual_ts:05.1f}s.png",
                            "detections": [],
                            "player_rows": []
                        }
                    else:
                        player_rows = map_to_player_rows(raw_ocr, img_height=840, img_width=1820)
                        ocr_data = {
                            "timestamp": actual_ts,
                            "filename": f"frame_{actual_ts:05.1f}s.png",
                            "detections": raw_ocr,
                            "player_rows": player_rows
                        }
                        last_ocr_crop = crop_bgr.copy()
                        last_ocr_data = ocr_data
                else:
                    ocr_data = {
                        "timestamp": actual_ts,
                        "filename": f"frame_{actual_ts:05.1f}s.png",
                        "detections": last_ocr_data["detections"],
                        "player_rows": last_ocr_data["player_rows"]
                    }

                aggregator.process_frame(timestamp=actual_ts, raw_ocr_data=ocr_data)

                # Check for state changes & build per-observation diagnostic log
                state_changes = []
                for pname in ["JAGDISH", "VISHAL", "TARUN"]:
                    pdata = aggregator.current_state["players"].get(pname, {})
                    ttl_now = pdata.get("ttl", {}).get("value", "-")
                    prev_summary = last_player_state_summary.get(pname, {})
                    prev_ttl = prev_summary.get("ttl", "-")

                    # Check frame roll changes
                    for f_i in range(1, 11):
                        fk = f"F{f_i}"
                        rolls_now = pdata.get("frames", {}).get(fk, {}).get("rolls", [])
                        prev_rolls = prev_summary.get("frames", {}).get(fk, {}).get("rolls", [])
                        if rolls_now and rolls_now != prev_rolls:
                            rolls_s = "/".join(rolls_now)
                            state_changes.append(f"{pname} {fk} -> {rolls_s}")

                    if ttl_now != "-" and ttl_now != prev_ttl and prev_ttl != "-":
                        state_changes.append(f"{pname} TTL -> {ttl_now}")

                    # Update player state summary
                    last_player_state_summary[pname] = {
                        "ttl": ttl_now,
                        "frames": {f"F{f_i}": {"rolls": list(pdata.get("frames", {}).get(f"F{f_i}", {}).get("rolls", []))} for f_i in range(1, 11)}
                    }

                print(f"[{actual_ts:5.1f}s]\nVISIBLE", flush=True)
                if state_changes:
                    for chg in state_changes:
                        print(f"  {chg}", flush=True)
                elif not need_ocr:
                    print("  state unchanged", flush=True)
                else:
                    dets_len = len(ocr_data.get("detections", []))
                    ttls_str = ", ".join([f"{p[:1]}={aggregator.current_state['players'].get(p, {}).get('ttl', {}).get('value', '-')}" for p in ["JAGDISH", "VISHAL", "TARUN"]])
                    print(f"  OCR detections: {dets_len} | TTLs: [{ttls_str}]", flush=True)

        frame_idx += 1

    cap.release()

    # Build clean output JSON according to specification
    print("\n[3/5] Exporting Final Structured Scoreboard to output/...")
    
    clean_players = []
    final_players_state = aggregator.current_state["players"]
    
    for pname in ["JAGDISH", "VISHAL", "TARUN"]:
        pdata = final_players_state.get(pname, {})
        frames_dict = {}
        for f_idx in range(1, 11):
            fk = f"F{f_idx}"
            f_info = pdata.get("frames", {}).get(fk, {})
            rolls = f_info.get("rolls", [])
            cum = f_info.get("cumulative")
            
            if not rolls and cum is None:
                frames_dict[str(f_idx)] = None
            else:
                frames_dict[str(f_idx)] = {
                    "rolls": rolls if rolls else [],
                    "cumulative": int(cum) if str(cum).isdigit() else cum
                }
        
        ttl_val = pdata.get("ttl", {}).get("value", "unknown")
        if str(ttl_val).isdigit():
            ttl_val = int(ttl_val)
            
        clean_players.append({
            "name": pname,
            "frames": frames_dict,
            "ttl": ttl_val
        })

    final_json_data = {
        "video": os.path.basename(video_path),
        "total_duration_seconds": round(duration, 2),
        "players": clean_players
    }

    out_json_path = os.path.join(args.output_dir, "final_scoreboard.json")
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(final_json_data, f, indent=2)
    print(f"  -> Saved clean JSON to: {out_json_path}")

    # Build clean output CSV
    out_csv_path = os.path.join(args.output_dir, "final_scoreboard.csv")
    with open(out_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["player", "frame", "rolls", "cumulative", "ttl"])
        for p in clean_players:
            pname = p["name"]
            ttl = p["ttl"]
            for f_idx in range(1, 11):
                f_data = p["frames"][str(f_idx)]
                if f_data is None:
                    rolls_str = "unplayed"
                    cum_str = "unplayed"
                else:
                    rolls_str = "/".join(f_data["rolls"]) if f_data["rolls"] else "-"
                    cum_str = f_data["cumulative"] if f_data["cumulative"] is not None else "unknown"
                writer.writerow([pname, f_idx, rolls_str, cum_str, ttl])
    print(f"  -> Saved clean CSV  to: {out_csv_path}")

    print("\n" + "=" * 70)
    print("FINAL DERIVED SCOREBOARD")
    print("=" * 70)
    for p in clean_players:
        print(f"{p['name']} -> TTL {p['ttl']}")
    print("=" * 70)
    
    for p in clean_players:
        print(f"\nPLAYER: {p['name']} (TTL: {p['ttl']})")
        for f_idx in range(1, 11):
            fd = p["frames"][str(f_idx)]
            if fd is None:
                print(f"  Frame {f_idx:2d}: UNPLAYED")
            else:
                rolls_str = "/".join(fd["rolls"]) if fd["rolls"] else "-"
                cum_str = fd["cumulative"] if fd["cumulative"] is not None else "unknown"
                print(f"  Frame {f_idx:2d}: Rolls=[{rolls_str:5s}] | Cumulative={cum_str}")

    print("\n" + "=" * 70)
    print("PIPELINE EXECUTION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
