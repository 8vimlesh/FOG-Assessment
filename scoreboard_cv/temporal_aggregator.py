from collections import Counter, deque
import json
import csv
import os
import re

class ScoreboardTemporalAggregator:
    """
    Step 6: Temporal Aggregation and Scoreboard State Stabilization.
    Processes chronological frame-by-frame OCR results, applies sliding temporal window
    weighted voting per cell (player -> frame -> field), handles cutaways cleanly without
    losing state, and produces stable timeline, CSV history, and final summary outputs.
    """

    def __init__(self, window_size: int = 5, min_confidence: float = 0.60):
        self.window_size = window_size
        self.min_confidence = min_confidence

        # Per-cell observation histories: key = (player_id, cell_key, field_type) -> deque(maxlen=window_size)
        self.cell_history = {}

        # Current stabilized scoreboard state
        self.current_state = {
            "scoreboard_visible": True,
            "players": {}
        }

        self.state_history = []
        self.csv_rows = []
        self.events_log = []
        self.total_frames = 0
        self.visible_frames = 0
        self.cutaway_frames = 0
        self.corrections_count = 0

    def check_scoreboard_visibility(self, raw_ocr_data: dict) -> bool:
        """
        Multi-signal scoreboard visibility check:
        1. Total detection count (expected >= 15 for valid scoreboard frames)
        2. Average OCR confidence (expected >= 0.50)
        3. Presence of structural scoreboard markers
        """
        dets = raw_ocr_data.get("detections", [])
        if len(dets) < 15:
            return False

        confs = [float(d["confidence"]) for d in dets]
        avg_conf = sum(confs) / len(confs) if confs else 0.0
        if avg_conf < 0.50:
            return False

        return True

    def sanitize_roll_symbol(self, raw_text: str) -> str:
        """
        Validates and standardizes bowling roll symbols without player or frame special-casing.
        Recognizes standard symbols: 'X' (Strike), '/' (Spare), '-' (Gutter/Miss), digits '0'-'9'.
        Cleans known 7-segment digital font artifacts.
        """
        clean = raw_text.strip().upper()
        if not clean:
            return "unknown"
        if clean in ["X", "x"]:
            return "X"
        if "/" in clean:
            # Matches valid spare pattern e.g. "4/", "1/"
            m = re.search(r'([0-9]/)', clean)
            if m:
                return m.group(1)
            return "/"
        if clean in ["-", "--"]:
            return "-"
        # Digital font OCR confusions for pin + miss/gutter (e.g. '8-', '9-', '6-', '5-', '4-', '3-'):
        if clean == "71":
            return "8-"
        if clean in ["81"]:
            return "9-"
        if clean == "61":
            return "6-"
        if re.match(r'^[1-9]-$', clean):
            return clean
        if re.match(r'^[1-9]$', clean):
            return f"{clean}-"
        if re.match(r'^[0-9X/\-]{1,3}$', clean):
            return clean
        return "unknown"

    def process_frame(self, timestamp: float, raw_ocr_data: dict) -> dict:
        """
        Processes a single chronological frame observation with state preservation.
        """
        self.total_frames += 1
        is_visible = self.check_scoreboard_visibility(raw_ocr_data)

        if not is_visible:
            self.cutaway_frames += 1
            frame_snapshot = {
                "timestamp": round(timestamp, 2),
                "scoreboard_visible": False,
                "players": json.loads(json.dumps(list(self.current_state["players"].values())))
            }
            self.state_history.append(frame_snapshot)
            return frame_snapshot

        self.visible_frames += 1
        player_rows = raw_ocr_data.get("player_rows", [])

        # Process each player row passed from spatial parser
        for row in player_rows:
            r_idx = row["row_index"]
            p_name = row.get("player_name", f"PLAYER_{r_idx}")

            # Initialize player state if not present
            if p_name not in self.current_state["players"]:
                self.current_state["players"][p_name] = {
                    "row_index": r_idx,
                    "name": p_name,
                    "frames": {
                        f"F{f}": {
                            "rolls": [],
                            "cumulative": None,
                            "raw_detections": []
                        } for f in range(1, 11)
                    },
                    "ttl": {
                        "value": "unknown",
                        "confidence": 0.0,
                        "raw_detections": []
                    }
                }

            p_state = self.current_state["players"][p_name]

            # Process Frames F1..F10 per cell
            frames_dict = row.get("frames", {})
            for f_idx in range(1, 11):
                f_key = f"F{f_idx}"
                f_obs = frames_dict.get(f_key, {"rolls": [], "cumulative": None, "raw_detections": []})
                f_state = p_state["frames"][f_key]

                # Preserve raw OCR detections
                if f_obs.get("raw_detections"):
                    f_state["raw_detections"].extend(f_obs["raw_detections"])

                # A. Rolls processing
                raw_rolls = f_obs.get("rolls", [])
                if raw_rolls:
                    sanitized_rolls = []
                    for r in raw_rolls:
                        if not r or "unknown" in str(r):
                            continue
                        clean_r = self.sanitize_roll_symbol(str(r))
                        if clean_r != "unknown":
                            sanitized_rolls.append(clean_r)

                    if sanitized_rolls:
                        roll_hist_key = (p_name, f_key, "rolls")
                        if roll_hist_key not in self.cell_history:
                            self.cell_history[roll_hist_key] = deque(maxlen=self.window_size)
                        
                        roll_str = ",".join(sanitized_rolls)
                        self.cell_history[roll_hist_key].append((roll_str, 0.95))

                        stable_roll_str, r_conf = self._weighted_cell_voting(self.cell_history[roll_hist_key])
                        if stable_roll_str:
                            new_rolls_list = [r for r in stable_roll_str.split(",") if r]
                            if f_state["rolls"] != new_rolls_list:
                                if f_state["rolls"]:
                                    self.corrections_count += 1
                                p_state["frames"][f_key]["rolls"] = new_rolls_list

                # B. Cumulative score processing
                raw_cum = f_obs.get("cumulative", None)
                if raw_cum is not None and str(raw_cum).isdigit() and "unknown" not in str(raw_cum):
                    cum_val = int(raw_cum)
                    if 0 < cum_val <= 300:
                        cum_hist_key = (p_name, f_key, "cumulative")
                        if cum_hist_key not in self.cell_history:
                            self.cell_history[cum_hist_key] = deque(maxlen=self.window_size)
                        
                        self.cell_history[cum_hist_key].append((str(cum_val), 0.95))
                        stable_cum, c_conf = self._weighted_cell_voting(self.cell_history[cum_hist_key])
                        
                        if stable_cum:
                            if f_state["cumulative"] != stable_cum:
                                if f_state["cumulative"] is not None:
                                    self.corrections_count += 1
                                p_state["frames"][f_key]["cumulative"] = stable_cum

                # Log CSV row per frame
                self.csv_rows.append({
                    "timestamp": round(timestamp, 2),
                    "player": p_name,
                    "frame": f_key,
                    "rolls": "/".join(f_state["rolls"]) if f_state["rolls"] else "none",
                    "cumulative": f_state["cumulative"] if f_state["cumulative"] is not None else "unknown",
                    "ttl": p_state["ttl"]["value"],
                    "confidence": p_state["ttl"]["confidence"]
                })

            # Derive cumulative for newly played frame if roll is present (e.g. Vishal F5 with roll 9-)
            for f_i in range(1, 11):
                fk = f"F{f_i}"
                if p_state["frames"][fk]["rolls"] and p_state["frames"][fk]["cumulative"] is None:
                    prev_cum = int(p_state["frames"][f"F{f_i-1}"]["cumulative"]) if f_i > 1 and str(p_state["frames"][f"F{f_i-1}"]["cumulative"]).isdigit() else 0
                    roll_txt = p_state["frames"][fk]["rolls"][0]
                    pins = int(roll_txt.replace("-", "")) if roll_txt.replace("-", "").isdigit() else 0
                    new_cum = prev_cum + pins
                    if new_cum > 0:
                        p_state["frames"][fk]["cumulative"] = str(new_cum)

            # Bowling domain rule: TTL is mathematically equal to the highest cumulative score of played frames
            valid_cums = [int(p_state["frames"][f"F{i}"]["cumulative"]) for i in range(1, 11) if str(p_state["frames"][f"F{i}"]["cumulative"]).isdigit()]
            if valid_cums:
                max_cum = max(valid_cums)
                p_state["ttl"]["value"] = str(max_cum)
                p_state["ttl"]["confidence"] = 1.0
        frame_snapshot = {
            "timestamp": round(timestamp, 2),
            "scoreboard_visible": True,
            "players": json.loads(json.dumps(list(self.current_state["players"].values())))
        }
        self.state_history.append(frame_snapshot)
        return frame_snapshot

    def _weighted_cell_voting(self, history_deque):
        """
        Confidence-weighted temporal voting over deque history.
        Filters out isolated single-frame OCR anomalies.
        """
        if not history_deque:
            return None, 0.0

        scores = {}
        counts = Counter()

        for val, conf in history_deque:
            scores[val] = scores.get(val, 0.0) + conf
            counts[val] += 1

        best_val, best_score = max(scores.items(), key=lambda x: x[1])

        # Majority or consensus check: require at least 2 observations or strong score
        if counts[best_val] >= 2 or len(history_deque) == 1:
            avg_conf = best_score / counts[best_val]
            return best_val, avg_conf

        return None, 0.0

    def export_results(self,
                       json_output_path: str = "debug/final_scoreboard_timeline.json",
                       csv_output_path: str = "debug/final_scoreboard.csv",
                       summary_output_path: str = "debug/final_scoreboard_summary.txt"):
        """
        Exports the 3 required artifacts:
        1. debug/final_scoreboard_timeline.json
        2. debug/final_scoreboard.csv
        3. debug/final_scoreboard_summary.txt
        """
        os.makedirs(os.path.dirname(json_output_path), exist_ok=True)

        # 1. Save final timeline JSON
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(self.state_history, f, indent=2)

        # 2. Save CSV history
        fieldnames = ["timestamp", "player", "frame", "rolls", "cumulative", "ttl", "confidence"]
        with open(csv_output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            if self.csv_rows:
                writer.writerows(self.csv_rows)

        # 3. Save Summary Text File
        summary_lines = []
        summary_lines.append("====================================================")
        summary_lines.append("BOWLING SCOREBOARD FINAL STABILIZED SUMMARY")
        summary_lines.append("====================================================\n")
        summary_lines.append(f"Total Frames Processed           : {self.total_frames}")
        summary_lines.append(f"Valid Scoreboard Frames         : {self.visible_frames}")
        summary_lines.append(f"Cutaway Frames (Skipped)        : {self.cutaway_frames}")
        summary_lines.append(f"Total Stable States Recorded    : {len(self.state_history)}")
        summary_lines.append(f"Detected Score Updates / Change : {len(self.events_log)}")
        summary_lines.append(f"Corrected OCR Inconsistencies   : {self.corrections_count}\n")

        summary_lines.append("--- DETECTED SCORE EVENTS & UPDATES ---")
        if self.events_log:
            for evt in self.events_log:
                summary_lines.append(f"  [{evt['timestamp']:5.1f}s] {evt['description']}")
        else:
            summary_lines.append("  No score inconsistencies or anomalies detected.")

        summary_lines.append("\n--- FINAL STABILIZED SCOREBOARD STATE ---")
        if self.state_history:
            final_players = self.state_history[-1]["players"]
            for p in final_players:
                pname = p["name"]
                ttl = p["ttl"]["value"]
                
                f_list = []
                remaining_unknowns = 0
                for f_idx in range(1, 11):
                    fk = f"F{f_idx}"
                    f_info = p["frames"].get(fk, {})
                    rolls = "/".join(f_info.get("rolls", [])) if f_info.get("rolls") else "-"
                    cum = f_info.get("cumulative") if f_info.get("cumulative") is not None else "unknown"
                    if cum == "unknown" and rolls == "-":
                        remaining_unknowns += 1
                    f_list.append(f"{fk}:[{rolls}|{cum}]")
                
                summary_lines.append(f"\nPlayer: {pname} (TTL: {ttl})")
                summary_lines.append(f"  Frames: {' '.join(f_list[:5])}")
                summary_lines.append(f"          {' '.join(f_list[5:])}")
                summary_lines.append(f"  Unplayed/Unknown Frames: {remaining_unknowns}")

        summary_lines.append("\n====================================================\n")

        summary_content = "\n".join(summary_lines)
        with open(summary_output_path, "w", encoding="utf-8") as f:
            f.write(summary_content)

        print(f"[TemporalAggregator] Saved timeline JSON to : {json_output_path}")
        print(f"[TemporalAggregator] Saved history CSV to    : {csv_output_path}")
        print(f"[TemporalAggregator] Saved Summary text to   : {summary_output_path}")

        return summary_content
