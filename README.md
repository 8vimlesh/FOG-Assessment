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

## Assessment Deliverables & Submission Format

### 1. GitHub Repository
- **Repository URL**: [https://github.com/8vimlesh/FOG-Assessment](https://github.com/8vimlesh/FOG-Assessment)
- **Input Benchmark Video**: [Download bowling_scoreboard.mp4 (Google Drive)](https://drive.google.com/file/d/1kOlGWIKtqkn6T_iLvBeZ51XTndfqTwIl/view?usp=sharing)
- Contains complete production source code, modular CV package (`scoreboard_cv/`), dependency manifest (`requirements.txt`), execution scripts, and verified JSON/CSV datasets.

### 2. Demo Video
- **Demo URL**: [▶ Watch Working Demo Video (Google Drive)](https://drive.google.com/file/d/1895Fc06iCq8DKqnsbnUxGxlF1NB_CcF6/view?usp=sharing)
- Comprehensive walkthrough demonstrating:
  1. Input video properties and lane broadcast framing
  2. CLI pipeline execution and runtime log streaming
  3. Scoreboard ROI detection, cutaway rejection, and preprocessing
  4. Deep learning OCR symbol detection and spatial 2D grid mapping
  5. Temporal aggregation and final extracted scoreboard datasets (Console, JSON, CSV)

### 3. Documentation PDF
- **PDF Report**: [`docs/FOG_Assessment_Documentation.pdf`](docs/FOG_Assessment_Documentation.pdf)
- Complete technical documentation with high-resolution visual screenshots, architectural diagrams, and mathematical consistency validation proofs.

---

## 📸 Pipeline Execution & Visual Evidence

### 1. Input Video Frame
![Input Video Frame](docs/figures/fig1_input_scoreboard_frame.png)
*Full HD (1920×1080 @ 30 FPS) broadcast frame showing the electronic overhead scoreboard above bowling lane 6.*

---

### 2. Scoreboard Detection & Spatial Grid Calibration

#### Detected Scoreboard ROI Crop
![Detected Scoreboard Crop](docs/figures/screenshot_detected_scoreboard.png)
*Detected and isolated overhead scoreboard region of interest (840×1820 px) with active player yellow highlight banner on Tarun.*

#### 2D Spatial Grid Calibration Overlay
![Spatial Grid Debug](docs/figures/fig2_spatial_grid_debug.png)
*2D spatial grid coordinate overlay partitioning all 4 player rows, 10 frame columns, roll/cumulative split lines, and TTL regions.*

---

### 3. Code Execution & Runtime Log Stream

#### Pipeline Startup & Deep Learning OCR Initialization
![Code Running - Pipeline Startup](docs/figures/screenshot_code_running_start.png)
*CLI execution startup: video ingestion (30.00 FPS, 1,735 frames, 57.83s duration) and PP-OCRv6 deep-learning model initialization.*

#### Frame Tracking & Symbol Extraction
![Code Running - Frame Tracking](docs/figures/screenshot_code_running_tracking.png)
*Frame-by-frame steady tracking extracting bowling symbols and cumulative totals across active frames.*

#### Adaptive Camera Cutaway Rejection
![Code Running - Cutaway Detection](docs/figures/screenshot_code_running_cutaway.png)
*Scoreboard visibility filter detecting broadcast cutaways (`HIDDEN/CUTAWAY`) during lane/pin action shots and freezing scoreboard state.*

#### Dynamic Mid-Match Score Progression
![Code Running - Dynamic Updates](docs/figures/screenshot_code_running_updates.png)
*Temporal state engine recognizing mid-match score updates as players complete subsequent frames.*

---

### 4. Extracted Scoreboard Data & Final Outputs

![Extracted Scoreboard Output](docs/figures/screenshot_extracted_output.png)
*Final extracted scoreboard data: complete multi-player matrix and standardized machine-readable JSON format.*

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

## Problem Statement & Challenges

Extracting structured bowling statistics from broadcast match video involves key technical challenges:

1. **Scoreboard Detection & ROI Extraction**: Accurately localizing the overhead electronic scoreboard display within 1080p broadcast frames.
2. **OCR Recognition of Bowling Symbols**: Recognizing low-resolution digital LED fonts, multi-digit rolls, strikes (`X`), spares (`/`), and misses (`-`).
3. **Spatial Grid Mapping**: Mapping 2D bounding boxes to 10 distinct frame columns and the TTL total column without column shift.
4. **Sub-Cell Partitioning**: Splitting each player-frame box into upper roll components and lower cumulative totals.
5. **Multi-Player Row Tracking**: Correctly associating numbers across 4 simultaneous player rows without row cross-talk.
6. **Camera Cutaway Handling**: Automatically classifying camera transitions away from the scoreboard and freezing state.
7. **Temporal State Aggregation**: Enforcing monotonic score accumulation and sliding-window consensus voting.
8. **Dynamic Name Discovery**: Discovering player names from header banners and active bowler highlight rows.

---

## Technology Stack

The production pipeline strictly uses the following stack:

- **Python**: 3.12 (Core pipeline runtime)
- **OpenCV (`opencv-python`)**: Video ingestion, frame capture, ROI cropping, Canny edge detection, CLAHE, and image filtering
- **NumPy**: Matrix operations, image differencing, array manipulation, and statistical metrics
- **PaddleOCR (`paddleocr`, `paddlepaddle`)**: Deep learning text detection (DBNet) and recognition (PP-OCRv6)
- **ReportLab (`reportlab`)**: Formal PDF report generation
- **JSON & CSV**: Structured dataset serialization

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
│   ├── FOG_Assessment_Documentation.pdf # Formal assessment PDF report with screenshots
│   ├── FINAL_REPORT.md              # Technical engineering assessment report
│   ├── build_pdf.py                 # ReportLab PDF build script
│   └── figures/                     # Documentation diagrams and visual figures
│
└── debug/                           # Supporting diagnostic and audit evidence
    ├── scoreboard_grid_debug.png    # Calibrated spatial grid diagnostic overlay
    ├── final_scoreboard_final_frame.png # Video frame capture of final scoreboard
    ├── final_validation_report.txt  # Automated accuracy validation report
    └── project_cleanup_audit.txt    # Codebase cleanup and audit log
```

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

### Run Main Pipeline:
```powershell
.venv\Scripts\python run_pipeline.py --video bowling_scoreboard.mp4
```

### Run Mathematical Consistency Validator:
```powershell
.venv\Scripts\python scoreboard_cv/validator.py
```

### Rebuild Documentation PDF:
```powershell
.venv\Scripts\python docs/build_pdf.py
```

---

## Mathematical Validation Report

```text
======================================================================
ROLL-VS-CUMULATIVE CONSISTENCY CHECK REPORT (output/final_scoreboard.json)
======================================================================
[PASS] TARUN   : F1=7 (61->7), F2=25 (1/->25 with next ball 8), F3=33 (8-->33), F4=40 (34->40)
[PASS] JAGDISH : F1=15 (X->15 with next frame 5-), F2=20 (5-->20), F3=27 (-7->27), F4=31 (4-->31), F5=41 (X->41)
[PASS] VISHAL  : F1=8 (8-->8), F2=11 (3-->11), F3=19 (71->19), F4=28 (81->28), F5=37 (9-->37)
[PASS] UNKNOWN_ROW_3 : F1=20 (X->20 with next frame 4/), F2=39 (4/->39 with next ball 9), F3=48 (9-->48), F4=54 (6-->54)
======================================================================
PASS: Zero mismatches found across all played frames.
======================================================================
```

---

## Author

**Vimlesh Tiwari**  
Candidate: Vimlesh Tiwari  
Role: Computer Vision Engineer Assessment  
Repository: [8vimlesh/FOG-Assessment](https://github.com/8vimlesh/FOG-Assessment)
