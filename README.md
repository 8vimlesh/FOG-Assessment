# BOWLING SCOREBOARD DATA EXTRACTION
## Computer Vision & OCR Based Video Analysis

**Candidate**: Vimlesh Tiwari  
**Role**: Computer Vision Engineer Assessment  
**Company**: FOG Technologies  
**Target Asset**: `bowling_scoreboard.mp4` (Full HD 1920×1080 @ 30 FPS)  
**Date**: August 2026  

---

## 1. Executive Summary & Problem Statement

### 1.1 Objective
The primary objective of this project is to develop an automated, end-to-end computer vision and optical character recognition (OCR) pipeline that extracts structured bowling scoreboard information from match video recordings.

The pipeline automatically analyzes the overhead electronic scoreboard display, identifies player rows, parses frame-by-frame roll symbols and cumulative scores, resolves temporal inconsistencies, and exports validated data in standardized JSON and CSV formats.

### 1.2 Target Information Extracted
- **Player Names**: Multi-player row association (`JAGDISH`, `VISHAL`, `TARUN`).
- **Frame Numbers**: Ten standard bowling frames (`F1` through `F10`).
- **Bowling Roll Symbols**: Strikes (`X`), Spares (`/`), Pin counts (`1`–`9`), Gutter/Foul/Miss (`-`).
- **Cumulative Frame Scores**: Incremental scores recorded at each completed frame.
- **Total Score (TTL)**: Current game total for each player.
- **Unplayed Frames**: Explicit preservation of future/unplayed frames (`null` in JSON, `unplayed` in CSV).

### 1.3 Core Computer Vision & Pipeline Challenges
1. **Camera Cutaways & Transitions**: The video switches between overhead scoreboard views and live bowling lane/pin action at multiple timestamps (~4–7s, ~23–26s, ~37–44s, ~49–52s). The pipeline must detect visibility states and avoid false detections during cutaways.
2. **OCR Noise & Font Artifacts**: High-contrast digital LED displays with small segmented fonts can introduce single-frame character confusion (e.g., confusing `X` with `*` or merged digits).
3. **Temporal Stabilization**: Single-frame OCR dropouts or false zeros must never corrupt previously verified game states. The system must maintain state monotonicity.
4. **Dynamic In-Game Updates**: New shots (such as Vishal completing Frame 5 late in the video) must be dynamically recognized and updated without overwriting prior history.

![Figure 1 — Broadcast video frame showing the three-player overhead scoreboard layout](figures/fig1_input_scoreboard_frame.png)
*Figure 1 — Broadcast video frame showing the three-player overhead scoreboard layout with active player rows, frame columns, and TTL displays.*

---

## 2. System Architecture

The pipeline implements a modular, high-throughput architecture combining visual preprocessing, deep learning OCR, spatial coordinate calibration, and temporal state aggregation.

```
+-------------------------------------------------------------------------------+
|                                INPUT VIDEO STREAM                             |
|                        (bowling_scoreboard.mp4, 1080p, 30 FPS)                |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
| 1. FRAME SAMPLING & EXTRACTION                                                |
|    - Uniform temporal sampling (~5 FPS / step = 6 frames)                     |
|    - Video metadata parsing: 1,735 total frames across 57.83 seconds          |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
| 2. SCOREBOARD ROI DETECTION & VISIBILITY FILTER                               |
|    - Overhead region extraction: Y[10:850], X[70:1890] (840 x 1820 ROI)       |
|    - Luminance & edge-energy checks for cutaway rejection                     |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
| 3. IMAGE PREPROCESSING & ENHANCEMENT                                          |
|    - Grayscale conversion & Contrast Limited Adaptive Histogram Equalization  |
|    - Bilateral edge-preserving denoising for digit clarity                    |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
| 4. DEEP LEARNING OCR (PaddleOCR 3.7.0 / PP-OCRv6)                             |
|    - Text box detection and alphanumeric recognition                          |
|    - Returns bounding boxes, transcribed text, and confidence scores          |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
| 5. SPATIAL GRID MAPPING & CELL ASSIGNMENT                                     |
|    - Bounding-box centroid classification: (center_x, center_y)               |
|    - Horizontal player row bins (Row 1, Row 2, Row 3)                         |
|    - Vertical frame column bins (Frames 1-10, Name, TTL)                      |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
| 6. CELL PARSING & SYMBOL CLASSIFICATION                                       |
|    - Sub-cell partitioning: roll symbols (upper) vs. cumulative scores (lower)|
|    - Bowling domain syntax normalization (X, /, numbers, -)                   |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
| 7. TEMPORAL STATE AGGREGATION & ARBITRATION                                   |
|    - Multi-frame sliding window consensus                                     |
|    - Monotonic score progression & transient error rejection                  |
|    - Preservation of unplayed frames                                          |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
| 8. STRUCTURED EXPORT & VALIDATION                                             |
|    - Machine-readable JSON (`output/final_scoreboard.json`)                   |
|    - Tabular CSV (`output/final_scoreboard.csv`)                              |
+-------------------------------------------------------------------------------+
```

---

## 3. Development & Environment Setup

The production pipeline is developed and executed within an isolated Python virtual environment configured with optimized computer vision and machine learning packages.

### 3.1 Environment Specification
- **Operating System**: Windows (64-bit)
- **Python Version**: Python 3.12.10
- **Virtual Environment**: `.venv`
- **Key Dependencies**:
  - `paddleocr >= 3.7.0`: Deep-learning text detection and recognition engine (PP-OCRv6).
  - `paddlepaddle >= 3.3.1`: Neural network inference runtime.
  - `opencv-python >= 4.10.0`: Video ingestion, ROI extraction, and image preprocessing.
  - `numpy >= 2.3.5`: Matrix operations and spatial coordinate calculations.
  - `reportlab >= 5.0.1`: PDF generation and documentation compilation.

![Figure 2 — Python 3.12 virtual environment and PaddleOCR engine verification](figures/fig3_env_setup_summary.png)
*Figure 2 — Python 3.12 virtual environment and PaddleOCR engine execution summary confirming zero-error initialization.*

---

## 4. Scoreboard Detection & Spatial Grid Mapping

### 4.1 Scoreboard ROI Extraction
The overhead display occupies a fixed 840 × 1820 pixel region within the 1920 × 1080 broadcast video stream (`ymin=10, ymax=850, xmin=70, xmax=1890`).

### 4.2 Centroid-Based Spatial Grid Calibration
Detected text tokens are mapped into structured player and frame cells using their normalized bounding-box centroids:

$$\text{center}_x = \frac{x_{\min} + x_{\max}}{2}, \quad \text{center}_y = \frac{y_{\min} + y_{\max}}{2}$$

#### Horizontal Player Row Boundaries ($Y$-Axis):
- **Header Row**: $0 \le Y < 135 \text{ px}$ (Lane metadata, frame labels 1–10, active bowler banner)
- **Row 1 (`JAGDISH`)**: $135 \le Y < 290 \text{ px}$
- **Row 2 (`VISHAL`)**: $290 \le Y < 447 \text{ px}$
- **Row 3 (`TARUN`)**: $447 \le Y < 840 \text{ px}$

#### Vertical Column Boundaries ($X$-Axis):
- **Player Name / Icon**: $0 \le X < 200 \text{ px}$
- **Frame 1**: $200 \le X < 340 \text{ px}$
- **Frame 2**: $340 \le X < 480 \text{ px}$
- **Frame 3**: $480 \le X < 620 \text{ px}$
- **Frame 4**: $620 \le X < 760 \text{ px}$
- **Frame 5**: $760 \le X < 900 \text{ px}$
- **Frames 6–10**: $900 \le X < 1620 \text{ px}$ ($140 \text{ px}$ per column)
- **TTL (Total Score)**: $1620 \le X \le 1820 \text{ px}$

![Figure 3 — Spatial grid calibration across player rows and frame columns](figures/fig2_spatial_grid_debug.png)
*Figure 3 — Spatial grid calibration and bounding-box overlay across player rows, frame columns, and TTL regions.*

![Figure 4 — Spatial Scoreboard Structure & Grid Mapping Calibration Report](figures/fig4_spatial_grid_report.png)
*Figure 4 — Spatial Scoreboard Structure & Grid Mapping Report confirming boundary calibration.*

---

## 5. Optical Character Recognition (OCR) Evaluation

OCR performance was benchmarked across representative video timestamps during evaluation to quantify detection rate, character recognition accuracy, and confidence metrics.

### 5.1 OCR Evaluation Metrics
- **Engine**: PaddleOCR 3.7.0 (PP-OCRv6)
- **Representative Timestamp Frames**: 6 samples (`0.0s`, `10.0s`, `20.0s`, `30.0s`, `40.0s`, `52.2s`)
- **Total Text Elements Detected**: 232 text elements
- **Overall Average Confidence**: **98.05%**

### 5.2 Per-Frame Evaluation Breakdown
| Timestamp | Frame ID | Detections | Avg Confidence | Notes / Scene Description |
|:---:|:---:|:---:|:---:|:---|
| **0.0s** | `frame0` | 47 | 98.77% | Stable overhead scoreboard view |
| **10.0s** | `frame300` | 40 | 97.73% | Stable overhead scoreboard view |
| **20.0s** | `frame600` | 42 | 97.52% | Stable overhead scoreboard view |
| **30.0s** | `frame900` | 50 | 98.75% | Scoreboard with active bowler indicator |
| **40.0s** | `frame1200` | 1 | 29.29% | Motion blur / lane cutaway (correctly rejected) |
| **52.2s** | `frame1566` | 52 | 98.71% | Scoreboard recovered; Vishal Frame 5 updated |

![Figure 5 — Quantitative OCR evaluation results and confidence metrics](figures/fig5_ocr_evaluation_results.png)
*Figure 5 — Quantitative OCR evaluation report showing 98.05% average confidence across representative timestamps.*

---

## 6. Temporal Aggregation & Cutaway Handling

### 6.1 Visibility & Cutaway Detection
Broadcast sporting events contain frequent camera angle switches. Overhead scoreboard frames exhibit high edge density across cell dividers and dark background luminance. When the broadcast cuts away to bowlers or pin decks (e.g. at ~40s):
- `is_scoreboard_visible` evaluates to `False`.
- Expensive OCR inference is bypassed.
- Current game state is locked and preserved without corruption.

### 6.2 Monotonic State Arbitration
Temporary OCR misreadings (e.g., reading a temporary `0` or dropped character during lighting changes) must not overwrite established scores. The temporal aggregator applies monotonic state validation:

$$\text{TTL}_{\text{new}} \ge \text{TTL}_{\text{previous}}$$

If an incoming observation reports $\text{TTL} = 0$ while the confirmed state is $\text{TTL} = 31$, the invalid observation is rejected, preserving scoreboard integrity.

### 6.3 Dynamic Frame Update: Vishal Frame 5
At timestamp $t \approx 52.2\text{s}$, player Vishal completes Frame 5, recording roll `9-` and updating cumulative score to `37` (Total `37`). The temporal aggregator captures this state change while keeping Jagdish and Tarun states stable.

![Figure 6 — Spatial cell mapping across video timeline showing temporal progression](figures/fig6_spatial_mapping_samples.png)
*Figure 6 — Spatial cell mapping across timestamps capturing state updates and cutaway handling.*

---

## 7. Production Pipeline Execution

The production pipeline (`run_pipeline.py`) provides an autonomous, single-command workflow processing the full video stream.

```bash
python run_pipeline.py --video bowling_scoreboard.mp4
```

### 7.1 Pipeline Execution Summary
- **Input Video**: `bowling_scoreboard.mp4`
- **Video Duration**: 57.83 seconds
- **Framerate**: 30.00 FPS
- **Total Video Frames**: 1,735 frames
- **Sampling Rate**: ~5 FPS (step = 6 frames)
- **Total Sampled Observations**: 290 observations
- **Two-Stage Optimization**: Frame-difference thresholding skips redundant OCR inference on static frames ($< 4.0$ pixel delta), achieving real-time processing speed.
- **Export Outputs**: Generated `output/final_scoreboard.json` and `output/final_scoreboard.csv`.

---

## 8. Final Derived Scoreboard

### 8.1 Final Game Totals
- **JAGDISH**: Total Score = **31**
- **VISHAL**: Total Score = **37**
- **TARUN**: Total Score = **54**

### 8.2 Comprehensive Scoreboard Matrix

| Player | Frame 1 | Frame 2 | Frame 3 | Frame 4 | Frame 5 | Frames 6–10 | Final TTL |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **JAGDISH** | `X` $\rightarrow$ 15 | `5-` $\rightarrow$ 20 | `-` $\rightarrow$ 27 | `4-` $\rightarrow$ 31 | *UNPLAYED* | *UNPLAYED* | **31** |
| **VISHAL** | `8-` $\rightarrow$ 8 | `3-` $\rightarrow$ 11 | `8-` $\rightarrow$ 19 | `9-` $\rightarrow$ 28 | `9-` $\rightarrow$ 37 | *UNPLAYED* | **37** |
| **TARUN** | `X` $\rightarrow$ 20 | `4/` $\rightarrow$ 39 | `9-` $\rightarrow$ 48 | `6-` $\rightarrow$ 54 | *UNPLAYED* | *UNPLAYED* | **54** |

*Note: Frames 6 through 10 were unplayed at the conclusion of the video clip and are explicitly recorded as unplayed.*

### 8.3 Structured Export Formats

#### JSON Output (`output/final_scoreboard.json`):
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
        "3": {"rolls": ["-"], "cumulative": 27},
        "4": {"rolls": ["4-"], "cumulative": 31},
        "5": null, "6": null, "7": null, "8": null, "9": null, "10": null
      },
      "ttl": 31
    },
    {
      "name": "VISHAL",
      "frames": {
        "1": {"rolls": ["8-"], "cumulative": 8},
        "2": {"rolls": ["3-"], "cumulative": 11},
        "3": {"rolls": ["8-"], "cumulative": 19},
        "4": {"rolls": ["9-"], "cumulative": 28},
        "5": {"rolls": ["9-"], "cumulative": 37},
        "6": null, "7": null, "8": null, "9": null, "10": null
      },
      "ttl": 37
    },
    {
      "name": "TARUN",
      "frames": {
        "1": {"rolls": ["X"], "cumulative": 20},
        "2": {"rolls": ["4/"], "cumulative": 39},
        "3": {"rolls": ["9-"], "cumulative": 48},
        "4": {"rolls": ["6-"], "cumulative": 54},
        "5": null, "6": null, "7": null, "8": null, "9": null, "10": null
      },
      "ttl": 54
    }
  ]
}
```

#### CSV Output (`output/final_scoreboard.csv`):
```csv
player,frame,rolls,cumulative,ttl
JAGDISH,1,X,15,31
JAGDISH,2,5-,20,31
JAGDISH,3,-,27,31
JAGDISH,4,4-,31,31
JAGDISH,5,unplayed,unplayed,31
...
VISHAL,5,9-,37,37
...
TARUN,4,6-,54,54
TARUN,5,unplayed,unplayed,54
```

---

## 9. Verification & Conclusion

### 9.1 Verification Checklist
- [x] Full HD video ingestion and temporal sampling (~5 FPS, 290 observations).
- [x] Scoreboard ROI isolation and adaptive cutaway rejection.
- [x] High-accuracy OCR text detection using PaddleOCR (98.05% average confidence).
- [x] Precise centroid-based spatial grid mapping across 3 players and 10 frames.
- [x] Robust temporal state arbitration preventing state resets during dropouts.
- [x] Accurate capture of dynamic mid-game events (Vishal Frame 5 score update).
- [x] Export to standard structured JSON and CSV files.

### 9.2 Concluding Statement
The implemented computer vision system successfully and reliably converts raw broadcast video footage into structured, temporally stabilized scoreboard data with zero manual intervention.
