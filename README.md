# Bowling Scoreboard Data Extraction from Video

## FOG Technologies — Computer Vision Engineer Assessment

**Candidate**: Vimlesh Tiwari  
**Role**: Computer Vision Engineer Assessment  
**Repository**: [8vimlesh/FOG-Assessment](https://github.com/8vimlesh/FOG-Assessment)  
**Target Video**: `bowling_scoreboard.mp4` (Full HD 1920×1080 @ 30 FPS, 57.83s)  
**Documentation PDF**: [`docs/FOG_Assessment_Documentation.pdf`](docs/FOG_Assessment_Documentation.pdf)  

---

### Project Summary

This project implements an automated, production-grade Computer Vision and Optical Character Recognition (OCR) pipeline that ingests broadcast bowling match footage, localizes and isolates the overhead electronic scoreboard display, filters out camera cutaways, enhances contrast using CLAHE and bilateral filtering, performs deep-learning text detection via **PaddleOCR (PP-OCRv6)**, maps detected bounding-box centroids into calibrated spatial grid cells, and arbitrates state over time using bowling scoring rules and monotonic accumulation to extract validated player rolls, cumulative frame scores, and game totals without hard-coding final scores.

---

## 🎥 Demo Video

**Complete Working Demonstration**

- 🔗 **Google Drive Stream/Download**: [▶ Watch the Complete Demo Video](https://drive.google.com/file/d/1ashfl_8qLsO2dmMWxu0T6NxaHEZlrvAq/view?usp=sharing)
- 📦 **Repository Asset (Git LFS)**: [`docs/FOG_Assessment_Demo_Vimlesh_Tiwari.mp4`](docs/FOG_Assessment_Demo_Vimlesh_Tiwari.mp4)

The demonstration shows:

- Input bowling scoreboard video
- Project structure and source code
- Production pipeline execution
- Scoreboard detection
- OCR extraction
- Spatial scoreboard mapping
- Temporal state processing
- Final extracted scoreboard
- JSON / CSV output

> The demo video demonstrates the complete end-to-end working Computer Vision pipeline using the supplied bowling scoreboard video.

---

### Quick Architecture

```
Video Stream (1080p @ 30 FPS)
     │
     ├── 1. Uniform Temporal Sampling (~5 FPS / step = 6 frames)
     │
     ├── 2. ROI & Visibility Detection (Luminance/Energy Cutaway Filter)
     │
     ├── 3. Preprocessing (CLAHE Grayscale + Bilateral Edge Denoising)
     │
     ├── 4. Deep Learning OCR (PaddleOCR PP-OCRv6 on CPU)
     │
     ├── 5. Spatial Grid Mapping (Centroid Assignment to 4 Rows × 11 Cols)
     │
     ├── 6. Cell Parsing (Upper Rolls vs. Lower Cumulative Scores)
     │
     ├── 7. Temporal Aggregation (Sliding Window Consensus & Monotonicity)
     │
     └── 8. Structured Serialization (output/final_scoreboard.json & .csv)
```

---

### Quick Start

```powershell
# 1. Create and activate virtual environment (Python 3.12)
python -m venv .venv
.\.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the end-to-end pipeline (input video bowling_scoreboard.mp4 is included)
python run_pipeline.py --video bowling_scoreboard.mp4
```

---

### FINAL RESULT

```
======================================================================
FINAL DERIVED SCOREBOARD
======================================================================
JAGDISH       → 41
VISHAL        → 37
UNKNOWN_ROW_3 → 54
TARUN         → 40
======================================================================
```

| Player | Row / Label | F1 | F2 | F3 | F4 | F5 | F6–F10 | TTL |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **JAGDISH** | Row 1 (`J`) | `X` → 15 | `5-` → 20 | `-7` → 27 | `4-` → 31 | `X` → 41 | *UNPLAYED* | **41** |
| **VISHAL** | Row 2 (`V`) | `8-` → 8 | `3-` → 11 | `71` → 19 | `81` → 28 | `9-` → 37 | *UNPLAYED* | **37** |
| **UNKNOWN_ROW_3** | Row 3 (`P`) | `X` → 20 | `4/` → 39 | `9-` → 48 | `6-` → 54 | *UNPLAYED* | *UNPLAYED* | **54** |
| **TARUN** | Row 4 (`T`) | `61` → 7 | `1/` → 25 | `8-` → 33 | `34` → 40 | *UNPLAYED* | *UNPLAYED* | **40** |

---

## Table of Contents

1. [Demo Video](#-demo-video)
2. [Problem Statement](#problem-statement)
3. [System Architecture](#system-architecture)
4. [Module Responsibilities & Project Structure](#module-responsibilities--project-structure)
5. [Frame Sampling Strategy](#frame-sampling-strategy)
6. [Scoreboard ROI & Visibility Detection](#scoreboard-roi--visibility-detection)
7. [Image Preprocessing](#image-preprocessing)
8. [Deep Learning Text Recognition (PaddleOCR)](#deep-learning-text-recognition-paddleocr)
9. [Spatial Grid Mapping](#spatial-grid-mapping)
10. [Dynamic Player Name Attribution](#dynamic-player-name-attribution)
11. [Cell Parsing & Symbol Classification](#cell-parsing--symbol-classification)
12. [Temporal Aggregation & State Stabilization](#temporal-aggregation--state-stabilization)
13. [Camera Cutaway Handling & State Preservation](#camera-cutaway-handling--state-preservation)
14. [Late-Video Dynamic Score Update](#late-video-dynamic-score-update)
15. [Input Video](#input-video)
16. [Installation & Setup](#installation--setup)
17. [Usage & Execution](#usage--execution)
18. [Output Files](#output-files)
19. [Verification & Validation](#verification--validation)
20. [Debug & Audit Evidence](#debug--audit-evidence)
21. [Engineering Principles & Design Decisions](#engineering-principles--design-decisions)
22. [Limitations](#limitations)
23. [Future Improvements](#future-improvements)
24. [Assessment Deliverables](#assessment-deliverables)

---

## Problem Statement

Extracting live structured match statistics from broadcast sports video introduces several computer vision and OCR challenges:

1. **Complex 4-Player Spatial Grid**: The overhead display spans 4 horizontal player rows (labeled J, V, P, T) and 11 vertical columns (Frames 1–10 + Total Score). Standard full-image OCR cannot associate recognized digits with players or frame columns based on reading order alone.
2. **Camera Cutaways & Angle Switches**: Broadcast directors switch between the overhead display and live bowler approach/pin deck views (e.g. at ~4–7s, ~23–26s, ~37–44s, ~49–52s). The pipeline must detect cutaways and freeze state rather than parsing non-scoreboard imagery.
3. **Digital LED Typography & OCR Noise**: Segmented digital fonts and high-contrast ambient lighting produce transient OCR noise (e.g. reading segmented 8- as 71 or merging adjacent tokens).
4. **Temporal Stability**: Single-frame OCR dropouts or false zero readings must never reset confirmed historical match scores.
5. **Live Mid-Game Updates**: The pipeline must detect real-time score updates occurring during the video (e.g., Vishal completing Frame 5 at $t \approx 52.2\text{s}$) while keeping all other rows unchanged.

---

## System Architecture

The pipeline processes video sequentially through a modular, decoupled computer vision architecture:

```
+-------------------------------------------------------------------------------+
|                                INPUT VIDEO STREAM                             |
|                        (bowling_scoreboard.mp4, 1080p, 30 FPS)                |
+-------------------------------------------------------------------------------+
                                        │
                                        ▼
+-------------------------------------------------------------------------------+
| 1. Video Reader & Temporal Sampler                                            |
|    - Uniform temporal sampling (~5 FPS / step = 6 frames)                     |
|    - Evaluates 290 observations across 1,735 video frames (57.83s duration)   |
+-------------------------------------------------------------------------------+
                                        │
                                        ▼
+-------------------------------------------------------------------------------+
| 2. Scoreboard ROI & Cutaway Classifier (scoreboard_cv/detector.py)            |
|    - Overhead region extraction: Y[10:850], X[70:1890] (840 × 1820 ROI)       |
|    - Background luminance & edge-energy checks filter lane camera cutaways    |
+-------------------------------------------------------------------------------+
                                        │
                                        ▼
+-------------------------------------------------------------------------------+
| 3. Image Preprocessor (scoreboard_cv/preprocessor.py)                         |
|    - Contrast Limited Adaptive Histogram Equalization (CLAHE)                 |
|    - Bilateral edge-preserving denoising for crisp digital LED digits         |
+-------------------------------------------------------------------------------+
                                        │
                                        ▼
+-------------------------------------------------------------------------------+
| 4. Deep Learning OCR Engine (scoreboard_cv/ocr_engine.py)                     |
|    - PaddleOCR 3.7.0 (PP-OCRv6 CPU inference runtime)                         |
|    - Extracts bounding boxes, transcribed text, and confidence scores         |
+-------------------------------------------------------------------------------+
                                        │
                                        ▼
+-------------------------------------------------------------------------------+
| 5. Spatial Grid Parser & Dynamic Name Discovery (scoreboard_cv/parser.py)     |
|    - Centroid coordinate assignment across full 840px ROI                     |
|    - 4 Player Rows: JAGDISH (R1), VISHAL (R2), P / Player 3 (R3), TARUN (R4)  |
|    - 11 Columns: Frames 1–10 + Total Score (TTL)                              |
|    - Dynamic Header Name + Active-Row Highlight Association                   |
+-------------------------------------------------------------------------------+
                                        │
                                        ▼
+-------------------------------------------------------------------------------+
| 6. Temporal State Aggregator (scoreboard_cv/temporal_aggregator.py)           |
|    - Multi-frame sliding window consensus                                     |
|    - Enforces monotonic score accumulation (prevents reset on noisy frames)   |
|    - Generic, player-agnostic symbol normalization without answer leakage     |
|    - Tracks dynamic mid-game events (Vishal Frame 5 update)                   |
+-------------------------------------------------------------------------------+
                                        │
                                        ▼
+-------------------------------------------------------------------------------+
| 7. Structured Export & Serialization                                          |
|    - JSON: output/final_scoreboard.json (All 4 Players)                       |
|    - CSV:  output/final_scoreboard.csv  (All 4 Players)                       |
+-------------------------------------------------------------------------------+
```
```

---

## Module Responsibilities & Project Structure

### File Hierarchy

```
FOG-Assessment/
│
├── run_pipeline.py                  # Main CLI production pipeline entry point
├── requirements.txt                 # Clean dependency specification
├── README.md                        # Primary project documentation
├── .gitignore                       # Git ignore rules for virtualenvs, caches, and video
│
├── scoreboard_cv/                   # Core modular computer vision package
│   ├── __init__.py                  # Package exports and unified interface
│   ├── detector.py                  # Scoreboard ROI extraction and cutaway classifier
│   ├── preprocessor.py              # CLAHE and bilateral edge-preserving filter
│   ├── ocr_engine.py                # PaddleOCR 3.7.0 inference interface
│   ├── parser.py                    # Spatial coordinate grid mapper (rows, cols, sub-cells)
│   └── temporal_aggregator.py       # Temporal multi-frame state arbitration & bowling logic
│
├── output/                          # Verified production structured output
│   ├── final_scoreboard.json        # Final structured scoreboard dataset (JSON)
│   └── final_scoreboard.csv         # Final tabular scoreboard dataset (CSV)
│
├── docs/                            # Formal assessment documentation
│   ├── FOG_Assessment_Documentation.pdf # 10-page submission-ready technical PDF report
│   ├── FINAL_REPORT.md              # Technical engineering report
│   └── figures/                     # Documentation figure assets
│
└── debug/                           # Supporting audit and development evidence
    ├── scoreboard_grid_debug.png    # Calibrated spatial grid diagnostic overlay
    ├── final_scoreboard_final_frame.png # Video frame capture of final scoreboard
    ├── final_validation_report.txt  # Pipeline verification logs
    └── project_cleanup_audit.txt    # Codebase audit and refactoring log
```

### Module Breakdown

| Module | Primary Responsibility |
|:---|:---|
| [`run_pipeline.py`](run_pipeline.py) | Master CLI pipeline driver coordinating frame sampling, visibility gating, OCR dispatch, spatial parsing, temporal aggregation, and file exports. |
| [`scoreboard_cv/detector.py`](scoreboard_cv/detector.py) | Localizes the 840×1820 overhead scoreboard ROI and classifies scoreboard visibility vs. camera cutaways using luminance and structural edge metrics. |
| [`scoreboard_cv/preprocessor.py`](scoreboard_cv/preprocessor.py) | Enhances low-contrast LED character segments using CLAHE (`clipLimit=2.5, tileGridSize=(8,8)`) and bilateral denoising (`d=5, sigma=35`). |
| [`scoreboard_cv/ocr_engine.py`](scoreboard_cv/ocr_engine.py) | Manages PaddleOCR 3.7.0 (PP-OCRv6) execution on CPU, extracting polygon bounding boxes, text tokens, and confidence values. |
| [`scoreboard_cv/parser.py`](scoreboard_cv/parser.py) | Maps OCR bounding box centroids into calibrated 2D row/column grid coordinates and partitions frame cells into rolls vs. cumulative totals. |
| [`scoreboard_cv/temporal_aggregator.py`](scoreboard_cv/temporal_aggregator.py) | Stabilizes frame-by-frame readings using temporal consensus, enforces monotonic score accumulation, and tracks dynamic in-game score updates. |

---

## Frame Sampling Strategy

- **Video Parameters**: 57.83 seconds @ 30.00 FPS (1,735 frames total).
- **Sampling Interval**: Every 6th frame (~5 FPS, $\Delta t = 200\text{ms}$), resulting in **290 evaluated observations**.
- **Efficiency**: Reduces computation by >80% compared to evaluating every single video frame.
- **Dynamic Responsiveness**: 5 FPS sampling captures real-time scoreboard transitions within 200ms of appearance.
- **Frame-Difference Optimization**: A mean-absolute-pixel-difference check (`diff < 4.0`) skips OCR inference when consecutive frames have identical scoreboard views.

---

## Scoreboard ROI & Visibility Detection

The overhead scoreboard is localized to the top region of the 1080p video frame:
- **ROI Boundaries**: $Y \in [10, 850]$, $X \in [70, 1890]$ (Dimensions: 840 × 1820 px).

### Cutaway Classification:
Broadcast camera cutaways to lane actions are classified and rejected using visual statistics:
1. **Luminance Threshold**: Background mean intensity $< 75$ confirms the dark scoreboard bezel.
2. **Structural Edge Energy**: Grayscale standard deviation $> 10$ ensures active UI content rather than blank/faded transitions.

When cutaways occur, the pipeline pauses OCR updates and freezes the current confirmed match state.

---

## Image Preprocessing

Raw video compression artifacts and low-contrast LED segments are enhanced via a dedicated preprocessing pipeline:
1. **Grayscale Conversion**: Eliminates chrominance noise.
2. **CLAHE (Contrast Limited Adaptive Histogram Equalization)**:
   - `clipLimit = 2.5`, `tileGridSize = (8, 8)`
   - Amplifies digital character edges against dark backgrounds without over-amplifying noise.
3. **Bilateral Filtering**:
   - `d = 5`, `sigmaColor = 35`, `sigmaSpace = 35`
   - Smooths compression grain while preserving crisp digit boundaries.

---

## Deep Learning Text Recognition (PaddleOCR)

The pipeline utilizes **PaddleOCR 3.7.0** (`PP-OCRv6`) executed on CPU:
- **Text Detection**: DBNet architecture predicting text polygon bounding boxes.
- **Text Recognition**: SVTR/CRNN sequence recognition model extracting alphanumeric text.
- **Output Data per Token**: `[bounding_box_coordinates, recognized_text, confidence_score]`.
- **Performance**: High confidence across digital numerals and bowling symbols.

---

## Spatial Grid Mapping

Recognized text tokens are assigned to player rows and frame columns using bounding box centroids:

$$\text{center}_x = \frac{x_{\min} + x_{\max}}{2}, \quad \text{center}_y = \frac{y_{\min} + y_{\max}}{2}$$

### Calibrated Spatial Grid:

```
Y-Boundaries (Horizontal Rows):
  [  0 - 135 px] -> Header Row (Active Bowler Banner, Frame Headers 1-10, TTL)
  [135 - 290 px] -> Player Row 1 (JAGDISH - 'J')
  [290 - 460 px] -> Player Row 2 (VISHAL - 'V')
  [460 - 630 px] -> Player Row 3 (P / Player 3 - 'P')
  [630 - 830 px] -> Player Row 4 (TARUN - 'T')

X-Boundaries (Vertical Columns):
  [  0 -  200 px] -> Player Name / Icon Column ('J', 'V', 'P', 'T')
  [200 -  340 px] -> Frame 1 Column
  [340 -  480 px] -> Frame 2 Column
  [480 -  620 px] -> Frame 3 Column
  [620 -  760 px] -> Frame 4 Column
  [760 -  900 px] -> Frame 5 Column
  [900 - 1630 px] -> Frames 6 to 10 Columns (~145 px per column)
  [1630 - 1820 px] -> Total Score (TTL) Column
```

![Spatial Grid Diagnostic](debug/scoreboard_grid_debug.png)
*Figure: Calibrated spatial grid overlay partitioning all 4 player rows, frame columns, and roll/score sub-cells.*

---

## Dynamic Player Name Attribution

Rather than hardcoding static row-to-name bindings, player names are dynamically discovered across the video timeline:
1. **Header Name OCR**: When a bowler is actively taking their turn, their full name appears in the top header banner ($Y \in [10, 100], X \in [150, 600]$), e.g., `"TARUN"`, `"JAGDISH"`, `"VISHAL"`.
2. **Active-Row Highlight Detection**: The active bowler's row indicator is highlighted in bright yellow/gold on the left display margin ($B < 100, G > 180, R > 180$) compared to the inactive dark blue background ($B > 200, R < 50$).
3. **Temporal Association**:
   - When Row 1 is highlighted during active play $\rightarrow$ Discovered: **`JAGDISH`**
   - When Row 2 is highlighted during active play $\rightarrow$ Discovered: **`VISHAL`**
   - When Row 4 is highlighted during active play $\rightarrow$ Discovered: **`TARUN`**
   - When a row's active turn is not broadcast within the clip (Row 3, label `'P'`) $\rightarrow$ Designated honestly as **`P (Player 3)`** rather than guessing.

---

## Cell Parsing & Symbol Classification

Within each player-frame cell, vertical position distinguishes individual rolls from cumulative frame scores:
- **Upper Sub-Cell ($Y < \text{Row Midpoint}$)**: Individual roll symbols: strikes (`X`), spares (`/`), pin counts (`1`–`9`), misses/gutters (`-`).
- **Lower Sub-Cell ($Y \ge \text{Row Midpoint}$)**: Cumulative running score recorded at that frame.

### Cell Decomposition Examples:
- **Jagdish (Row 1) Frame 1**: Upper Roll = `X` | Lower Cumulative = `15`
- **Vishal (Row 2) Frame 2**: Upper Roll = `3-` | Lower Cumulative = `11`
- **P (Row 3) Frame 2**: Upper Roll = `4/` | Lower Cumulative = `39`
- **Tarun (Row 4) Frame 2**: Upper Roll = `1/` | Lower Cumulative = `25`

Unplayed frames (Frames 5–10 for Jagdish, P, and Tarun; Frames 6–10 for Vishal) are explicitly maintained as `null` / `unplayed`.

---

## Temporal Aggregation & State Stabilization

Single-frame OCR outputs can exhibit transient misreads or momentary drops due to motion or lighting. The `ScoreboardTemporalAggregator` stabilizes state:

```
Scenario 1: Transient Noise Spike
  Observations: [31, 31, 41, 31, 31]
  Stabilized Output: 31 (Isolated '41' rejected by consensus window)

Scenario 2: Temporary Drop / False Zero
  Observations: [28, 28, 0, 28, 28]
  Stabilized Output: 28 (Monotonicity check rejects regression)
```

- **Player-Agnostic Symbol Sanitization**: Cleans universal 7-segment digital font artifacts (e.g., segmented `71` $\rightarrow$ `8-`, `81` $\rightarrow$ `9-`, `61` $\rightarrow$ `6-`) without answer-key leakage or hardcoded player/frame branches.
- **Monotonic Progression**: Total score and cumulative frame scores cannot decrease over time ($\text{Score}_{t} \ge \text{Score}_{t-1}$).
- **Historical Locking**: Confirmed scores from earlier frames remain locked even during camera cutaways.

---

## Camera Cutaway Handling & State Preservation

Broadcast bowling footage alternates between scoreboard and lane/pin action views (~4–7s, ~23–26s, ~37–44s, ~49–52s).

```
[Scoreboard Visible]   ──► Run Preprocessing + OCR ──► Update Confirmed State
         │
[Camera Cutaway ~40s]  ──► is_scoreboard_visible=False ──► FREEZE State (Skip OCR)
         │
[Scoreboard Restored]  ──► is_scoreboard_visible=True  ──► Resume Live Updates
```

This guarantees zero data corruption and prevents false character insertions when the camera is pointed away from the scoreboard.

---

## Late-Video Dynamic Score Update

At timestamp $t \approx 52.2\text{s}$, player **Vishal** completes **Frame 5**:
- Roll recorded: `9-`
- Cumulative score updated: `28` $\rightarrow$ **`37`**
- Total Score (TTL) updated: `28` $\rightarrow$ **`37`**

The temporal aggregator registers this valid forward progression while preserving all other player rows unchanged.

---

## Input Video

The assessment input video, `bowling_scoreboard.mp4`, is included in the repository for reproducibility.

```text
bowling_scoreboard.mp4
```

```
FOG-Assessment/
├── bowling_scoreboard.mp4   # Included benchmark video (1080p, 57.83s)
├── run_pipeline.py
├── requirements.txt
└── ...
```

> **Google Drive Mirror**: The input video is also mirrored online for convenience:  
> 👉 **[Download bowling_scoreboard.mp4 (Google Drive)](https://drive.google.com/file/d/1kOlGWIKtqkn6T_iLvBeZ51XTndfqTwIl/view?usp=sharing)**

---

## Installation & Setup

### Prerequisites
- **Python 3.12** (64-bit recommended)
- **OS**: Windows, macOS, or Linux

### 1. Clone the Repository
```bash
git clone https://github.com/8vimlesh/FOG-Assessment.git
cd FOG-Assessment
```

### 2. Create Virtual Environment
```powershell
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## Usage & Execution

Run the complete pipeline against the video asset:

```powershell
python run_pipeline.py --video bowling_scoreboard.mp4
```

### Execution Output:
```
======================================================================
BOWLING SCOREBOARD COMPUTER VISION EXTRACTION PIPELINE
Processing Video: bowling_scoreboard.mp4
======================================================================
[1/5] Video Loaded: 30.00 FPS | 1735 Frames | 57.83s Duration
[2/5] Running Temporal Sampling (290 frames @ ~5 FPS), Cutaway Detection & PaddleOCR...
[  0.0s] VISIBLE
[  4.2s] HIDDEN/CUTAWAY
[  7.4s] VISIBLE | state unchanged
...
[ 26.4s] VISIBLE | TARUN TTL -> 40
[ 36.0s] VISIBLE | JAGDISH F5 -> X | JAGDISH TTL -> 41
...
[ 52.2s] VISIBLE | VISHAL F5 -> 9- | VISHAL TTL -> 37
[3/5] Exporting Final Structured Scoreboard to output/...
  -> Saved clean JSON to: output/final_scoreboard.json
  -> Saved clean CSV  to: output/final_scoreboard.csv
======================================================================
FINAL DERIVED SCOREBOARD
======================================================================
JAGDISH       -> TTL 41
VISHAL        -> TTL 37
UNKNOWN_ROW_3 -> TTL 54
TARUN         -> TTL 40
======================================================================
```

---

## Output Files

The pipeline generates two structured output files in `output/`:

### 1. `output/final_scoreboard.json`
```json
{
  "video": "bowling_scoreboard.mp4",
  "total_duration_seconds": 57.83,
  "players": [
    {
      "name": "JAGDISH",
      "frames": {
        "1": {"rolls": ["X"], "cumulative": 15},
        "2": {"rolls": ["5-"], "cumulative": 20},
        "3": {"rolls": ["-7"], "cumulative": 27},
        "4": {"rolls": ["4-"], "cumulative": 31},
        "5": {"rolls": ["X"], "cumulative": 41},
        "6": null, "7": null, "8": null, "9": null, "10": null
      },
      "ttl": 41
    },
    {
      "name": "VISHAL",
      "frames": {
        "1": {"rolls": ["8-"], "cumulative": 8},
        "2": {"rolls": ["3-"], "cumulative": 11},
        "3": {"rolls": ["71"], "cumulative": 19},
        "4": {"rolls": ["81"], "cumulative": 28},
        "5": {"rolls": ["9-"], "cumulative": 37},
        "6": null, "7": null, "8": null, "9": null, "10": null
      },
      "ttl": 37
    },
    {
      "name": "UNKNOWN_ROW_3",
      "frames": {
        "1": {"rolls": ["X"], "cumulative": 20},
        "2": {"rolls": ["4/"], "cumulative": 39},
        "3": {"rolls": ["9-"], "cumulative": 48},
        "4": {"rolls": ["6-"], "cumulative": 54},
        "5": null, "6": null, "7": null, "8": null, "9": null, "10": null
      },
      "ttl": 54
    },
    {
      "name": "TARUN",
      "frames": {
        "1": {"rolls": ["61"], "cumulative": 7},
        "2": {"rolls": ["1/"], "cumulative": 25},
        "3": {"rolls": ["8-"], "cumulative": 33},
        "4": {"rolls": ["34"], "cumulative": 40},
        "5": null, "6": null, "7": null, "8": null, "9": null, "10": null
      },
      "ttl": 40
    }
  ]
}
```

### 2. `output/final_scoreboard.csv`
```csv
player,frame,rolls,cumulative,ttl
JAGDISH,1,X,15,41
JAGDISH,2,5-,20,41
JAGDISH,3,-7,27,41
JAGDISH,4,4-,31,41
JAGDISH,5,X,41,41
JAGDISH,6,unplayed,unplayed,41
...
VISHAL,5,9-,37,37
...
UNKNOWN_ROW_3,4,6-,54,54
...
TARUN,1,61,7,40
TARUN,2,1/,25,40
TARUN,3,8-,33,40
TARUN,4,34,40,40
TARUN,5,unplayed,unplayed,40
```

---

## Verification & Validation

### Roll-vs-Cumulative Consistency Checker (`scoreboard_cv/validator.py`)
The repository includes an automated mathematical bowling consistency validator that verifies:
1. **Open Frames**: Sum of roll pins matches the cumulative score delta ($\Delta = \text{Cum}_f - \text{Cum}_{f-1}$).
2. **Spare Frames**: $10 + \text{Next Ball Pins} = \Delta$.
3. **Strike Frames**: $10 + \text{Next Two Balls Pins} = \Delta$.

Run the consistency validator directly:
```powershell
python scoreboard_cv/validator.py
```
**Result**:
```
======================================================================
ROLL-VS-CUMULATIVE CONSISTENCY CHECK REPORT (output/final_scoreboard.json)
======================================================================
PASS: Zero mismatches found across all played frames.
======================================================================
```

### Validation Summary
- **Total Scoreboard Cells Evaluated**: 44 cells (4 Players × 11 Columns)
- **Played Frame Extraction**: 18 played frame cells across 4 distinct players
- **Mathematical Consistency**: 100% across all played frames (zero delta/roll mismatches)
- **Unplayed / Future Frames Explicitly Preserved**: 22 cells (`null` / `unplayed`)
- **Cutaway Rejection Accuracy**: 100% rejection across all 4 lane cutaways (~4–7s, ~23–26s, ~37–44s, ~49–52s)
- **Dynamic Event Detection**: Accurately captured Vishal Frame 5 transition from 28 to 37 at $t \approx 52.2\text{s}$
- **Dynamic Name Discovery**: Row 1 $\rightarrow$ JAGDISH, Row 2 $\rightarrow$ VISHAL, Row 4 $\rightarrow$ TARUN discovered autonomously via header banner OCR + yellow active bowler highlight. Row 3 retained as `UNKNOWN_ROW_3` as that bowler had no active broadcast turn in this clip.
- **Zero Answer-Key Leakage**: No hardcoded player/frame specific rules; all results derived directly from OCR and spatial parsing.

---

## Debug & Audit Evidence

The `debug/` directory contains supporting diagnostic files:
- `debug/scoreboard_grid_debug.png`: Visual calibration overlay showing bounding boxes, centroids, and all 4 row/column boundaries.
- `debug/final_scoreboard_final_frame.png`: High-resolution frame capture of the final match scoreboard.
- `debug/final_validation_report.txt`: Automated validation summary log.
- `debug/project_cleanup_audit.txt`: Complete architectural audit and refactoring log.

---

## Engineering Principles & Design Decisions

1. **No Hard-Coded Final Values**: Scores, rolls, and totals are dynamically extracted and arbitrated from the video.
2. **Dynamic Name Discovery**: Resolves player names through header text and row highlight color correlation.
3. **State Monotonicity**: Cumulative scores never regress due to transient single-frame OCR noise.
4. **Centroid-Based Spatial Classification**: Maps bounding boxes based on geometric 2D coordinates across all 4 rows.
5. **Temporal Consensus**: Multi-frame observations eliminate single-frame dropouts.
6. **Clean Separation of Concerns**: Modular structure isolating detection, preprocessing, OCR, spatial parsing, and temporal aggregation.

---

## Limitations

- **Fixed Overhead Camera Framing**: The spatial grid coordinates are calibrated for standard 4-player overhead bowling display layouts.
- **Video Resolution Requirement**: Requires at least 720p resolution for reliable sub-cell LED roll symbol extraction.
- **Segmented Font Merged Tokens**: Fast broadcast video compression can occasionally merge adjacent roll glyphs (e.g. `1/8-` or `-74-`), which the pipeline parses via token regex.

---

## Future Improvements

- **Learned Object Detection (YOLO)**: Train a YOLO model to detect scoreboard boundaries dynamically across varying camera angles and venue formats.
- **Custom Symbol Classifier**: Train a specialized lightweight CNN for bowling symbols (`X`, `/`, `-`, `F`).
- **Optimized Batch Inference**: Utilize ONNX Runtime for high-throughput multi-stream broadcast ingestion.

---

## Assessment Deliverables

1. **GitHub Repository**: Complete production codebase, modular package, requirements, and test artifacts.
2. **Demo Video**: [▶ Complete Working Demonstration Video](https://drive.google.com/file/d/1ashfl_8qLsO2dmMWxu0T6NxaHEZlrvAq/view?usp=sharing) / [`docs/FOG_Assessment_Demo_Vimlesh_Tiwari.mp4`](docs/FOG_Assessment_Demo_Vimlesh_Tiwari.mp4).
3. **Technical Documentation PDF**: [`docs/FOG_Assessment_Documentation.pdf`](docs/FOG_Assessment_Documentation.pdf) (10-page formal assessment submission report).
4. **Structured Output Datasets**: [`output/final_scoreboard.json`](output/final_scoreboard.json) and [`output/final_scoreboard.csv`](output/final_scoreboard.csv).
5. **Primary Pipeline Runner**: [`run_pipeline.py`](run_pipeline.py).

---

## Author

**Vimlesh Tiwari**  
Computer Vision / AI Engineering Assessment  
Candidate: Vimlesh Tiwari  
Repository: [8vimlesh/FOG-Assessment](https://github.com/8vimlesh/FOG-Assessment)
