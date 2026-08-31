import cv2
import numpy as np
import warnings

# Suppress runtime warnings for clean output
warnings.filterwarnings("ignore")

class ScoreboardOCRProcessor:
    """
    PaddleOCR-based text and digit recognition engine for bowling scoreboard analysis.
    Takes a preprocessed scoreboard image crop (path or numpy array) and returns
    structured bounding box detections.
    """

    def __init__(self, engine_name: str = "paddleocr"):
        self.paddle_ocr = None
        self._init_paddleocr()

    def _init_paddleocr(self):
        try:
            from paddleocr import PaddleOCR
            print("[OCRProcessor] Initializing PaddleOCR engine...")
            self.paddle_ocr = PaddleOCR(
                lang='en',
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                enable_mkldnn=False
            )
            print("[OCRProcessor] PaddleOCR engine ready.")
        except Exception as e:
            raise RuntimeError(
                f"PaddleOCR failed to initialize ({e}). Run the pipeline using the repository "
                r"virtual environment: .venv\Scripts\python run_pipeline.py"
            ) from e

    def run_ocr(self, img_input) -> list:
        """
        Runs OCR on image file path or numpy array and returns standardized detection list:
        [ {"text": str, "confidence": float, "bbox": [[x1,y1],[x2,y1],[x2,y2],[x1,y2]]}, ... ]
        """
        detections = []

        if self.paddle_ocr is None:
            return detections

        try:
            if hasattr(self.paddle_ocr, "predict"):
                res = list(self.paddle_ocr.predict(img_input))
            else:
                res = list(self.paddle_ocr.ocr(img_input))

            if res and len(res) > 0 and res[0] is not None:
                item = res[0]
                # Format for PaddleOCR 3.x / Paddlex (dict)
                if isinstance(item, dict):
                    texts = item.get("rec_texts", [])
                    scores = item.get("rec_scores", [])
                    polys = item.get("rec_polys", item.get("dt_polys", []))
                    for text, score, poly in zip(texts, scores, polys):
                        t_str = str(text).strip()
                        if t_str:
                            bbox = [[int(pt[0]), int(pt[1])] for pt in poly]
                            detections.append({
                                "text": t_str,
                                "confidence": round(float(score), 4),
                                "bbox": bbox
                            })
                    return detections
                # Format for PaddleOCR 2.x (list of lines)
                elif isinstance(item, list):
                    for line in item:
                        bbox = [[int(pt[0]), int(pt[1])] for pt in line[0]]
                        text = str(line[1][0]).strip()
                        conf = float(line[1][1])
                        if text:
                            detections.append({
                                "text": text,
                                "confidence": round(conf, 4),
                                "bbox": bbox
                            })
                    return detections
        except Exception as e:
            print(f"[OCRProcessor] PaddleOCR execution notice: {e}")

        return detections
