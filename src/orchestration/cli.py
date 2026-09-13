#!/usr/bin/env python3
"""RAG Ingestion Pipeline - Entry Point

Usage:
    python -m src.orchestration.cli --source-dir ./data/raw/billing
    OR
    python src/orchestration/cli.py --source-dir ./data/raw/billing
"""
from __future__ import annotations

import os
import sys

# Add project root to path so 'src' package is discoverable
# __file__ -> cli.py -> src/orchestration -> src/orchestration -> project root
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.ingestion.pipeline import main


if __name__ == "__main__":
    main()