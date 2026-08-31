# Bowling Scoreboard Data Extraction from Video

## FOG Technologies — Computer Vision Engineer Assessment

**Candidate**: Vimlesh Tiwari  
**Role**: Computer Vision Engineer Assessment  
**Repository**: [8vimlesh/FOG-Assessment](https://github.com/8vimlesh/FOG-Assessment)  
**Target Video**: `bowling_scoreboard.mp4` (Full HD 1920×1080 @ 30.00 FPS, 57.83s duration, 1,735 frames)  
**Documentation PDF**: [`docs/FOG_Assessment_Documentation.pdf`](docs/FOG_Assessment_Documentation.pdf)  

---

## 🎥 Final Demo Video

[▶ Watch Final Working Demo](https://drive.google.com/file/d/1895Fc06iCq8DKqnsbnUxGxlF1NB_CcF6/view?usp=sharing)

> The final demo demonstrates the complete end-to-end working solution, including the input bowling scoreboard video, project/code execution, scoreboard detection and OCR extraction, spatial scoreboard mapping, temporal processing, and the final structured scoreboard output.

---

## Assessment Deliverables

### 1. GitHub Repository

**Repository URL**: [https://github.com/8vimlesh/FOG-Assessment](https://github.com/8vimlesh/FOG-Assessment)

The repository contains:
- Complete production source code and modules
- Comprehensive `README.md` documentation
- Dependency manifest (`requirements.txt`)
- Benchmark input bowling scoreboard video (`bowling_scoreboard.mp4`)
- Modular Computer Vision package (`scoreboard_cv/`)
- Scoreboard detection & visibility cutaway filter (`detector.py`)
- Contrast enhancement & noise reduction preprocessing (`preprocessor.py`)
- PaddleOCR deep-learning text recognition with environment validation (`ocr_engine.py`)
- Calibrated 2D spatial grid coordinate parser (`parser.py`)
- Confidence-weighted temporal state aggregator (`temporal_aggregator.py`)
- Mathematical consistency validator (`validator.py`)
- Structured JSON output dataset ([`output/final_scoreboard.json`](output/final_scoreboard.json))
- Tabular CSV output dataset ([`output/final_scoreboard.csv`](output/final_scoreboard.csv))
- Visual spatial grid calibration and audit reports in `debug/`
- Formal 10-page assessment technical report ([`docs/FOG_Assessment_Documentation.pdf`](docs/FOG_Assessment_Documentation.pdf))

### 2. Demo Video

[▶ Watch Final Working Demo](https://drive.google.com/file/d/1895Fc06iCq8DKqnsbnUxGxlF1NB_CcF6/view?usp=sharing)

The demonstration covers:
1. Input video overview and properties
2. Project directory structure and codebase walkthrough
3. End-to-end CLI execution of `run_pipeline.py`
4. Scoreboard ROI localization and cutaway rejection
5. Preprocessing and PaddleOCR deep-learning symbol detection
6. Spatial grid centroid assignment and sub-cell roll/cumulative splitting
7. Temporal state processing, consensus voting, and dynamic score updates
8. Final structured scoreboard output (Console, JSON, and CSV)

### 3. Documentation

**PDF Report**: [`docs/FOG_Assessment_Documentation.pdf`](docs/FOG_Assessment_Documentation.pdf)

The documentation PDF provides formal diagrams, explanations, and visual evidence for:
- Input broadcast video frames and framing geometry
- Pipeline runtime execution and diagnostic logs
- Detected and cropped scoreboard region of interest (ROI)
- OCR text detection bounding boxes and token extractions
- Final structured scoreboard outputs in JSON and CSV formats

---

## Project Overview

This project extracts structured bowling scoreboard information from video using Computer Vision and OCR.

The pipeline performs:

```
Video Stream (1080p @ 30 FPS)
     │
     ├── 1. Uniform Temporal Sampling (~5 FPS / step = 6 frames)
     │
     ├── 2. Scoreboard ROI Extraction (840 × 1820 px region)
     │
     ├── 3. Visibility & Cutaway Detection (Luminance + Edge Gradient Energy)
     │
     ├── 4. Image Preprocessing (CLAHE Grayscale + Bilateral Edge Denoising)
     │
     ├── 5. PaddleOCR Inference (PP-OCRv6 Deep Learning Text Recognition)
     │
     ├── 6. Spatial Grid Mapping (Centroid Assignment to 4 Rows × 11 Columns)
     │
     ├── 7. Cell Parsing (Upper Rolls vs. Lower Cumulative Scores)
     │
     ├── 8. Temporal Aggregation (Confidence-Weighted Voting & State Preservation)
     │
     └── 9. JSON / CSV Export (Standardized Structured Datasets)
```

---

## Final Result

Extracted directly from the verified production outputs ([`output/final_scoreboard.json`](output/final_scoreboard.json) and [`output/final_scoreboard.csv`](output/final_scoreboard.csv)):

### Player Summary

| Player | Final TTL |
|---|---:|
| **JAGDISH** | 41 |
| **VISHAL** | 37 |
| **UNKNOWN_ROW_3** (Player 3) | 54 |
| **TARUN** | 40 |

### Detailed Frame-by-Frame Results

| Player | Row / Label | F1 | F2 | F3 | F4 | F5 | F6 | F7 | F8 | F9 | F10 | TTL |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **JAGDISH** | Row 1 (`J`) | `X` (15) | `5-` (20) | `-7` (27) | `4-` (31) | `X` (41) | *unplayed* | *unplayed* | *unplayed* | *unplayed* | *unplayed* | **41** |
| **VISHAL** | Row 2 (`V`) | `8-` (8) | `3-` (11) | `71` (19) | `81` (28) | `9-` (37) | *unplayed* | *unplayed* | *unplayed* | *unplayed* | *unplayed* | **37** |
| **UNKNOWN_ROW_3** | Row 3 (`P`) | `X` (20) | `4/` (39) | `9-` (48) | `6-` (54) | *unplayed* | *unplayed* | *unplayed* | *unplayed* | *unplayed* | *unplayed* | **54** |
| **TARUN** | Row 4 (`T`) | `61` (7) | `1/` (25) | `8-` (33) | `34` (40) | *unplayed* | *unplayed* | *unplayed* | *unplayed* | *unplayed* | *unplayed* | **40** |

*Note: In the benchmark video clip, Frames 6 through 10 (as well as Frame 5 for Row 3 and Tarun) were unplayed at match conclusion and are explicitly preserved as `null` in JSON and `unplayed` in CSV. Row 3 had no active broadcast bowler turn in the clip and is honestly preserved as `UNKNOWN_ROW_3`.*

---

## Problem Statement

Extracting structured bowling statistics from broadcast match video involves key technical challenges:

1. **Detecting the Scoreboard Region**: Accurately localizing the overhead electronic scoreboard display within high-definition broadcast frames.
2. **OCR Recognition of Bowling Symbols**: Recognizing low-resolution digital LED fonts, multi-digit rolls, strikes (`X`), spares (`/`), and misses (`-`).
3. **Mapping Detections to Frame Columns**: Reliably mapping 2D bounding boxes to 10 distinct frame columns and the TTL total column without column shift.
4. **Separating Roll Symbols from Cumulative Scores**: Splitting each player-frame box into upper roll components and lower cumulative totals.
5. **Handling Multiple Scoreboard Rows**: Correctly associating numbers across 4 simultaneous player rows without row cross-talk.
6. **Handling Temporary OCR Noise**: Filtering transient single-frame OCR dropouts or false characters without corrupting valid historical frames.
7. **Handling Camera Cutaways**: Automatically classifying camera transitions away from the scoreboard (lane, pin deck, bowler reactions) and pausing updates.
8. **Preserving Previous Valid Scoreboard State**: Locking established scores during cutaways and ensuring monotonic score accumulation.

---

## Technology Stack

The production pipeline strictly uses the following stack:

- **Python**: 3.12 (Core pipeline runtime)
- **OpenCV (`opencv-python`)**: Video ingestion, frame capture, ROI cropping, Canny edge detection, CLAHE, and image filtering
- **NumPy**: Matrix operations, image differencing, array manipulation, and statistical metrics
- **PaddleOCR (`paddleocr`, `paddlepaddle`)**: Deep learning text detection (DBNet) and recognition (PP-OCRv6)
- **JSON**: Structured JSON dataset serialization
- **CSV**: Tabular CSV dataset export
- **Regular Expressions (`re`)**: Token validation, digit extraction, and bowling roll pattern recognition

---

## Project Structure

```
FOG-Assessment/
│
├── run_pipeline.py                  # Main CLI production entry point and orchestrator
├── requirements.txt                 # Clean dependency specification
├── README.md                        # Comprehensive project documentation
├── bowling_scoreboard.mp4           # Benchmark match video (1080p, 30 FPS, 57.83s)
├── .gitignore                       # Git ignore configuration
│
├── scoreboard_cv/                   # Core modular computer vision package
│   ├── __init__.py                  # Package exports and interface
│   ├── detector.py                  # Scoreboard ROI extraction and cutaway classifier
│   ├── preprocessor.py              # CLAHE contrast enhancement and bilateral filter
│   ├── ocr_engine.py                # PaddleOCR engine wrapper with environment validation
│   ├── parser.py                    # Spatial 2D coordinate grid mapper and name discovery
│   ├── temporal_aggregator.py       # Temporal state stabilization, voting, and bowling rules
│   └── validator.py                 # Automated mathematical roll-vs-cumulative consistency checker
│
├── output/                          # Generated structured output datasets
│   ├── final_scoreboard.json        # Clean structured JSON scoreboard dataset
│   └── final_scoreboard.csv         # Clean tabular CSV scoreboard dataset
│
├── docs/                            # Documentation artifacts
│   ├── FOG_Assessment_Documentation.pdf # 10-page formal assessment PDF report
│   ├── FINAL_REPORT.md              # Technical engineering assessment report
│   └── figures/                     # Documentation diagrams and visual figures
│
└── debug/                           # Supporting diagnostic and audit evidence
    ├── scoreboard_grid_debug.png    # Calibrated spatial grid diagnostic overlay
    ├── final_scoreboard_final_frame.png # Video frame capture of final scoreboard
    ├── final_validation_report.txt  # Automated accuracy validation report
    └── project_cleanup_audit.txt    # Codebase cleanup and audit log
```

---

## Module Documentation

### `scoreboard_cv/detector.py`
- **Scoreboard ROI Extraction**: Crops the overhead electronic display region ($Y \in [10, 850], X \in [70, 1890]$) from 1080p frames.
- **Scoreboard Visibility Detection**: Evaluates Canny edge density ($> 0.028$) and top header luminance ($70 \le \mu \le 130$) to verify scoreboard presence.
- **Camera Cutaway Handling**: Rejects broadcast cuts to lane action, pin decks, and player close-ups, signaling the aggregator to freeze state.

### `scoreboard_cv/preprocessor.py`
- **Image Enhancement**: Converts ROI crops to grayscale for luminance analysis.
- **Contrast Improvement**: Applies Contrast Limited Adaptive Histogram Equalization (CLAHE, `clipLimit=2.5, tileGridSize=(8,8)`).
- **Noise Reduction**: Employs bilateral filtering (`d=5, sigma=35`) to suppress video compression artifacts while preserving sharp digital LED digit edges.
- **OCR Preparation**: Writes enhanced grayscale crops ready for deep-learning OCR inference.

### `scoreboard_cv/ocr_engine.py`
- **PaddleOCR Initialization**: Configures and boots PaddleOCR with the PP-OCRv6 CPU inference runtime.
- **OCR Inference**: Ingests preprocessed frames and returns structured bounding boxes, transcribed text tokens, and confidence scores.
- **Environment Validation**: Validates that all required deep learning libraries are installed and operational.
- **Explicit Failure Handling**: Raises an explicit, actionable `RuntimeError` if PaddleOCR fails to initialize, preventing silent degradation into empty outputs.

### `scoreboard_cv/parser.py`
- **Spatial Scoreboard Grid**: Partitions the 840px ROI into 4 horizontal player rows and 11 vertical columns (F1–F10 + TTL).
- **Player Row Detection**: Assigns detections to Row 1 ($[135, 290)$), Row 2 ($[290, 460)$), Row 3 ($[460, 630)$), and Row 4 ($[630, 830)$).
- **Frame Column Mapping**: Resolves $X$-coordinates into columns ($F1 \in [200, 340), \dots, \text{TTL} \in [1630, 1820]$).
- **TTL Mapping**: Captures total match scores from the rightmost column.
- **Roll / Cumulative Separation**: Uses calibrated vertical split lines per row to classify upper text as individual rolls and lower text as cumulative frame totals.
- **Multi-Column De-merging**: Splits horizontally merged LED tokens across frame boundaries using character-interpolated positions.
- **Dynamic Name Discovery**: Extracts bowler names from the top banner ($Y \in [10, 100], X \in [150, 600]$) and correlates them with yellow active-bowler row highlights.

### `scoreboard_cv/temporal_aggregator.py`
- **Temporal State Aggregation**: Accumulates frame observations across chronological video time.
- **Confidence-Weighted Voting**: Uses sliding-window consensus voting to eliminate transient single-frame OCR misreads.
- **OCR Noise Handling**: Cleans universal 7-segment digital font anomalies (e.g., `-7`, `5-`, `81`, `4/`).
- **State Preservation**: Enforces monotonic accumulation ($\text{Score}_t \ge \text{Score}_{t-1}$) so historical scores never regress.
- **Cutaway Handling**: Freezes match state during cutaways, ensuring zero false insertions while camera is off the scoreboard.
- **Prevention of State Overwrites**: Blocks invalid or empty observations from overwriting confirmed match state.
- **Dynamic In-Game Updates**: Automatically detects forward progress when a bowler completes a new frame late in the video.

### `run_pipeline.py`
- **Main Production Entry Point**: Orchestrates CLI arguments, input video loading, and output directory setup.
- **Video Processing**: Performs uniform temporal sampling (~5 FPS, step = 6 frames) across 1,735 frames.
- **Frame-Difference Optimization**: Skips redundant OCR computation when consecutive frames are visually static (`diff < 4.0`).
- **Pipeline Orchestration**: Seamlessly connects detector, preprocessor, OCR engine, spatial parser, and temporal aggregator.
- **Output Generation**: Serializes final validated outputs to `output/final_scoreboard.json` and `output/final_scoreboard.csv`.
- **Diagnostic Logging**: Prints timestamped state transition logs during execution.

---

## Input Video

- **File**: `bowling_scoreboard.mp4`
- **Resolution**: 1920 × 1080 (Full HD)
- **Frame Rate**: 30.00 FPS
- **Total Frames**: 1,735 frames
- **Total Duration**: 57.83 seconds
- **Availability**: Included locally in the repository root.
- **Online Mirror**: 👉 **[Download bowling_scoreboard.mp4 (Google Drive)](https://drive.google.com/file/d/1kOlGWIKtqkn6T_iLvBeZ51XTndfqTwIl/view?usp=sharing)**

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

### 2. Set Up Virtual Environment & Dependencies
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
```

*(For macOS / Linux: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`)*

---

## Usage & Execution

Run the complete pipeline:

```powershell
.venv\Scripts\python run_pipeline.py --video bowling_scoreboard.mp4
```

### Automated Verification
Run the mathematical roll-vs-cumulative consistency validator:
```powershell
.venv\Scripts\python scoreboard_cv/validator.py
```

---

## Output Files

1. **[`output/final_scoreboard.json`](output/final_scoreboard.json)**:
   Structured JSON recording each player, played frames (with roll lists and cumulative scores), unplayed frames (`null`), and final TTL totals.
2. **[`output/final_scoreboard.csv`](output/final_scoreboard.csv)**:
   Tabular CSV format recording `player`, `frame`, `rolls`, `cumulative`, and `ttl`.

---

## Author

**Vimlesh Tiwari**  
Candidate: Vimlesh Tiwari  
Role: Computer Vision Engineer Assessment  
Repository: [8vimlesh/FOG-Assessment](https://github.com/8vimlesh/FOG-Assessment)
