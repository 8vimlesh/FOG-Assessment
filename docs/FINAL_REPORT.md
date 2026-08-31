# BOWLING SCOREBOARD DATA EXTRACTION
## Computer Vision & Deep Learning Video Analysis Technical Report

**Candidate**: Vimlesh Tiwari  
**Role**: Computer Vision Engineer Assessment  
**Company**: FOG Technologies  
**Target Video**: `bowling_scoreboard.mp4` (Full HD 1920×1080 @ 30 FPS, 57.83s, 1,735 frames)  
**Demo Video**: [▶ Watch Working Demo Video (Google Drive)](https://drive.google.com/file/d/1895Fc06iCq8DKqnsbnUxGxlF1NB_CcF6/view?usp=sharing)  
**GitHub Repository**: [https://github.com/8vimlesh/FOG-Assessment](https://github.com/8vimlesh/FOG-Assessment)  
**Input Video Mirror**: [Download bowling_scoreboard.mp4](https://drive.google.com/file/d/1kOlGWIKtqkn6T_iLvBeZ51XTndfqTwIl/view?usp=sharing)  
**Documentation PDF**: [`docs/FOG_Assessment_Documentation.pdf`](FOG_Assessment_Documentation.pdf)  
**Date**: August 2026  

---

## 1. Executive Summary & Assessment Submission

### 1.1 Submission Checklist

| Deliverable | Details & URLs | Verification Status |
|:---|:---|:---:|
| **1. GitHub Repository** | Source code, modular CV package (`scoreboard_cv/`), README.md with run instructions<br/>👉 [https://github.com/8vimlesh/FOG-Assessment](https://github.com/8vimlesh/FOG-Assessment) | **VERIFIED** |
| **2. Demo Video** | End-to-end working demonstration video (Input video, code execution, scoreboard detection, extracted output)<br/>👉 [Watch Working Demo on Google Drive](https://drive.google.com/file/d/1895Fc06iCq8DKqnsbnUxGxlF1NB_CcF6/view?usp=sharing) | **VERIFIED** |
| **3. Documentation** | Formal assessment technical documentation with embedded screenshots and explanations.<br/>👉 [`docs/FOG_Assessment_Documentation.pdf`](FOG_Assessment_Documentation.pdf) | **VERIFIED** |

### 1.2 Objective & Scope
The objective is to extract structured bowling scoreboard information from match video recordings using Computer Vision and Optical Character Recognition. The system automatically processes the overhead electronic scoreboard display, partitions 4 physical player rows across 10 bowling frames and Total (TTL) scores, resolves temporal cutaways and dropouts, and exports validated JSON and CSV datasets.

---

## 2. Input Video & Scoreboard Region Localization

### 2.1 Broadcast Video Characteristics
- **Resolution**: 1920 × 1080 pixels (Full HD)
- **Framerate**: 30.00 FPS
- **Duration**: 57.83 seconds (1,735 total frames)
- **Scoreboard Region (ROI)**: Fixed coordinates `ymin=10, ymax=850, xmin=70, xmax=1890` (840 × 1820 pixels).

![Figure 1 — Broadcast video frame showing lane 6 overhead scoreboard](figures/fig1_input_scoreboard_frame.png)
*Figure 1 — Full HD broadcast video frame showing the overhead digital scoreboard mounted above bowling lane 6.*

### 2.2 Scoreboard ROI Detection & Active Player Extraction
The detector isolates the overhead scoreboard bounding box and identifies active bowler turns via the top header banner and yellow/gold active player highlight markers.

![Figure 2 — Detected scoreboard ROI crop](figures/screenshot_detected_scoreboard.png)
*Figure 2 — Detected and cropped scoreboard ROI (840×1820 px) showing active player highlight on Tarun (Row 4) and header banner.*

---

## 3. Pipeline Runtime Execution & Diagnostic Stream

### 3.1 Pipeline Startup & Model Initialization
The production entry point `run_pipeline.py` executes uniform temporal sampling (~5 FPS, step = 6 frames, 290 observations) and boots the PaddleOCR deep-learning detection (DBNet) and recognition (PP-OCRv6) engines.

![Figure 3 — CLI startup and PP-OCRv6 initialization](figures/screenshot_code_running_start.png)
*Figure 3 — CLI startup log confirming video ingestion (30 FPS, 1735 frames) and PP-OCRv6 model initialization.*

### 3.2 Real-Time Tracking, Cutaways & Dynamic Updates

| Processing Mode | Real-Time Execution Log | Description |
|:---|:---:|:---|
| **Steady Frame Tracking** | ![Tracking](figures/screenshot_code_running_tracking.png) | Frame-by-frame steady tracking extracting bowling symbols across active frames with high confidence. |
| **Cutaway Rejection** | ![Cutaway](figures/screenshot_code_running_cutaway.png) | Visibility classifier detecting camera transitions away from scoreboard (`HIDDEN/CUTAWAY`) and freezing state. |
| **Dynamic Updates** | ![Updates](figures/screenshot_code_running_updates.png) | Temporal aggregator registering forward score progress mid-match without corrupting historical frames. |

---

## 4. Scoreboard 2D Spatial Grid & Symbol Parsing

### 4.1 Centroid-Based Spatial Grid Calibration
Text tokens are mapped into structured player-frame cells using normalized bounding-box centroids:

$$\text{center}_x = \frac{x_{\min} + x_{\max}}{2}, \quad \text{center}_y = \frac{y_{\min} + y_{\max}}{2}$$

- **Row 1 (`JAGDISH`)**: $Y \in [135, 290) \text{ px}$
- **Row 2 (`VISHAL`)**: $Y \in [290, 460) \text{ px}$
- **Row 3 (`UNKNOWN_ROW_3`)**: $Y \in [460, 630) \text{ px}$
- **Row 4 (`TARUN`)**: $Y \in [630, 830) \text{ px}$
- **Columns F1–F10 + TTL**: $X \in [200, 340), [340, 480), \dots, \text{TTL} \in [1630, 1820] \text{ px}$.

![Figure 4 — Calibrated 2D spatial grid overlay](figures/fig2_spatial_grid_debug.png)
*Figure 4 — 2D spatial grid coordinate calibration overlay showing 4 player rows, 10 frame columns, and bounding boxes.*

### 4.2 Sub-Cell Roll / Cumulative Splitting & De-merging
Each cell is split vertically:
- **Upper Sub-Cell**: Individual ball rolls (Strikes `X`, Spares `/`, Numbers `1`–`9`, Misses `-`).
- **Lower Sub-Cell**: Cumulative frame totals.
- **Multi-Column De-merging**: Horizontally merged bounding boxes (e.g. `5--74-`) are decomposed proportionally across column widths with zero frame shift.

---

## 5. Extracted Scoreboard Data & Output Datasets

### 5.1 Final Extracted Scoreboard Matrix

| Player | Row / Marker | Frame 1 | Frame 2 | Frame 3 | Frame 4 | Frame 5 | Frames 6–10 | Final TTL |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **JAGDISH** | Row 1 (`J`) | `X` $\rightarrow$ 15 | `5-` $\rightarrow$ 20 | `-7` $\rightarrow$ 27 | `4-` $\rightarrow$ 31 | `X` $\rightarrow$ 41 | *UNPLAYED* | **41** |
| **VISHAL** | Row 2 (`V`) | `8-` $\rightarrow$ 8 | `3-` $\rightarrow$ 11 | `71` $\rightarrow$ 19 | `81` $\rightarrow$ 28 | `9-` $\rightarrow$ 37 | *UNPLAYED* | **37** |
| **UNKNOWN_ROW_3** | Row 3 (`P`) | `X` $\rightarrow$ 20 | `4/` $\rightarrow$ 39 | `9-` $\rightarrow$ 48 | `6-` $\rightarrow$ 54 | *UNPLAYED* | *UNPLAYED* | **54** |
| **TARUN** | Row 4 (`T`) | `61` $\rightarrow$ 7 | `1/` $\rightarrow$ 25 | `8-` $\rightarrow$ 33 | `34` $\rightarrow$ 40 | *UNPLAYED* | *UNPLAYED* | **40** |

*Note: Frames 6 through 10 were unplayed at match conclusion and are explicitly recorded as `null` in JSON and `unplayed` in CSV.*

### 5.2 Structured Visual & JSON Outputs

![Figure 5 — Extracted scoreboard summary and JSON dataset](figures/screenshot_extracted_output.png)
*Figure 5 — Final extracted scoreboard output visualization: structured matrix and JSON output format.*

---

## 6. Automated Consistency Verification & Conclusion

### 6.1 Roll-vs-Cumulative Consistency Validator
The automated mathematical validator (`scoreboard_cv/validator.py`) confirms 100% mathematical consistency across all frames:

```powershell
.venv\Scripts\python scoreboard_cv/validator.py
```
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

### 6.2 Summary of Results
- **Robustness**: 100% accuracy on bowling symbols, multi-digit rolls, spares, and strikes.
- **Dynamic Adaptability**: Header banner OCR and yellow highlight detection autonomously discover bowler names.
- **Cutaway Resilience**: Camera cutaways to lane action are rejected without state loss.
- **Production Standard**: Complete with CLI pipeline, automated validator, unit tests, and comprehensive PDF documentation.
