"""
Bowling Scoreboard Computer Vision & OCR Extraction Package
"""

from .detector import is_scoreboard_visible, extract_scoreboard_roi
from .preprocessor import preprocess_pipeline_clahe
from .ocr_engine import ScoreboardOCRProcessor
from .parser import map_to_player_rows
from .temporal_aggregator import ScoreboardTemporalAggregator

__all__ = [
    "is_scoreboard_visible",
    "extract_scoreboard_roi",
    "preprocess_pipeline_clahe",
    "ScoreboardOCRProcessor",
    "map_to_player_rows",
    "ScoreboardTemporalAggregator",
]

__version__ = "1.0.0"
