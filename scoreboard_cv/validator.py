import re
import json
from typing import Dict, List, Any, Optional

def parse_roll_pins(roll_str: str) -> List[int]:
    """
    Converts a roll symbol/string into a list of pin counts:
    - 'X' -> [10]
    - '-' -> [0]
    - '4/' -> [4, 6]
    - '1/' -> [1, 9]
    - '/' -> [10]
    - '6-' -> [6, 0]
    - '-7' -> [0, 7]
    - '61' -> [6, 1]
    - '34' -> [3, 4]
    - '81' -> [8, 1]
    - '5'  -> [5, 0]
    """
    if not roll_str or roll_str == "unplayed" or roll_str == "-":
        return []
    
    clean = str(roll_str).strip().upper()
    if clean == "X":
        return [10]
    if clean in ["-", "--"]:
        return [0]
    
    # Spare e.g. "4/", "1/"
    m_spare = re.match(r'^([0-9])/$', clean)
    if m_spare:
        d1 = int(m_spare.group(1))
        return [d1, 10 - d1]
    if clean == "/":
        return [10]
    
    # Miss on ball 1, pins on ball 2: e.g. "-7", "-4"
    m_miss_first = re.match(r'^\-([0-9])$', clean)
    if m_miss_first:
        return [0, int(m_miss_first.group(1))]
    
    # Pins on ball 1, miss on ball 2: e.g. "6-", "5-"
    m_miss_second = re.match(r'^([0-9])\-$', clean)
    if m_miss_second:
        return [int(m_miss_second.group(1)), 0]
    
    # Two digits e.g. "61", "34", "81"
    m_two_digits = re.match(r'^([0-9])([0-9])$', clean)
    if m_two_digits:
        return [int(m_two_digits.group(1)), int(m_two_digits.group(2))]
    
    # Single digit
    if re.match(r'^[0-9]$', clean):
        return [int(clean), 0]
    
    return []

def validate_scoreboard_consistency(scoreboard_data: dict) -> List[Dict[str, Any]]:
    """
    Validates roll vs. cumulative consistency across all players in the scoreboard.
    Evaluates:
    - Open frames (non-carry): sum(rolls) must equal cumulative delta
    - Spare frames (with next ball available): 10 + next_ball_1 must equal cumulative delta
    - Strike frames (with next 2 balls available): 10 + next_ball_1 + next_ball_2 must equal cumulative delta
    """
    mismatches = []
    players = scoreboard_data.get("players", [])

    for player in players:
        p_name = player.get("name", "Unknown")
        frames = player.get("frames", {})

        # Collect rolls and cum per frame
        parsed_frames = {}
        for f_idx in range(1, 11):
            fk = str(f_idx)
            f_data = frames.get(fk)
            if f_data:
                raw_rolls = f_data.get("rolls", [])
                cum_val = f_data.get("cumulative")
                roll_str = "/".join(raw_rolls) if isinstance(raw_rolls, list) else str(raw_rolls)
                pins = []
                if isinstance(raw_rolls, list):
                    for r in raw_rolls:
                        pins.extend(parse_roll_pins(r))
                else:
                    pins = parse_roll_pins(roll_str)
                cum_int = int(cum_val) if cum_val is not None and str(cum_val).isdigit() else None
                parsed_frames[f_idx] = {
                    "rolls_str": roll_str,
                    "pins": pins,
                    "cumulative": cum_int,
                    "is_strike": ("X" in roll_str.upper()),
                    "is_spare": ("/" in roll_str)
                }

        prev_cum = 0
        for f_idx in range(1, 11):
            if f_idx not in parsed_frames:
                continue

            curr = parsed_frames[f_idx]
            cum_int = curr["cumulative"]
            if cum_int is None:
                continue

            actual_delta = cum_int - prev_cum
            roll_str = curr["rolls_str"]
            pins = curr["pins"]

            # 1. Open Frame (Not Strike, Not Spare)
            if not curr["is_strike"] and not curr["is_spare"]:
                expected_delta = sum(pins)
                if expected_delta != actual_delta:
                    mismatches.append({
                        "player": p_name,
                        "frame": f_idx,
                        "type": "OPEN",
                        "rolls": roll_str,
                        "expected_delta": expected_delta,
                        "actual_delta": actual_delta,
                        "prev_cumulative": prev_cum,
                        "curr_cumulative": cum_int,
                        "error": f"Open frame sum(rolls)={expected_delta} vs actual delta={actual_delta}"
                    })

            # 2. Spare Frame: 10 + next frame ball 1
            elif curr["is_spare"]:
                next_f = parsed_frames.get(f_idx + 1)
                if next_f and next_f["pins"]:
                    next_ball_1 = next_f["pins"][0]
                    expected_delta = 10 + next_ball_1
                    if expected_delta != actual_delta:
                        mismatches.append({
                            "player": p_name,
                            "frame": f_idx,
                            "type": "SPARE",
                            "rolls": roll_str,
                            "expected_delta": expected_delta,
                            "actual_delta": actual_delta,
                            "prev_cumulative": prev_cum,
                            "curr_cumulative": cum_int,
                            "error": f"Spare frame (10 + {next_ball_1})={expected_delta} vs actual delta={actual_delta}"
                        })

            # 3. Strike Frame: 10 + next 2 balls
            elif curr["is_strike"]:
                next_f = parsed_frames.get(f_idx + 1)
                if next_f and len(next_f["pins"]) >= 2:
                    bonus = next_f["pins"][0] + next_f["pins"][1]
                    expected_delta = 10 + bonus
                    if expected_delta != actual_delta:
                        mismatches.append({
                            "player": p_name,
                            "frame": f_idx,
                            "type": "STRIKE",
                            "rolls": roll_str,
                            "expected_delta": expected_delta,
                            "actual_delta": actual_delta,
                            "prev_cumulative": prev_cum,
                            "curr_cumulative": cum_int,
                            "error": f"Strike frame (10 + {bonus})={expected_delta} vs actual delta={actual_delta}"
                        })

            prev_cum = cum_int

    return mismatches

def check_scoreboard_file(json_path: str = "output/final_scoreboard.json") -> List[Dict[str, Any]]:
    """
    Loads final_scoreboard.json and runs consistency validation.
    Prints all mismatches found.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    mismatches = validate_scoreboard_consistency(data)
    
    print("=" * 70)
    print(f"ROLL-VS-CUMULATIVE CONSISTENCY CHECK REPORT ({json_path})")
    print("=" * 70)
    if not mismatches:
        print("PASS: Zero mismatches found across all played frames.")
    else:
        print(f"FAILED: Found {len(mismatches)} mismatch(es):")
        for m in mismatches:
            print(f"  [Player: {m['player']:15s}] Frame {m['frame']:2d} ({m.get('type','OPEN')}): Rolls='{m['rolls']:6s}' | Expected Delta={m['expected_delta']}, Actual Delta={m['actual_delta']} (Cum: {m['prev_cumulative']} -> {m['curr_cumulative']})")
    print("=" * 70)
    return mismatches

if __name__ == "__main__":
    check_scoreboard_file()
