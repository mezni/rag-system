#!/usr/bin/env python3
"""RAG Ingestion Pipeline - Entry Point

Usage:
    python -m src.orchestration.cli --source-dir ./data/raw/billing
    OR
    python src/orchestration/cli.py --source-dir ./data/raw/billing
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Add project root to path so 'src' package is discoverable
# __file__ -> cli.py -> src/orchestration -> src/orchestration -> project root
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.ingestion.pipeline import run_ingestion, Settings


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG Ingestion Pipeline")
    parser.add_argument("--source-dir", type=Path, required=True,
                        help="Directory to scan for documents")
    args = parser.parse_args()

    # Create dummy settings for environment loading without DATABASE_URL requirement
    os.environ.setdefault("DATABASE_URL", "none")
    settings = Settings()

    if not args.source_dir.exists():
        print(f"Error: Source directory does not exist: {args.source_dir}", file=sys.stderr)
        sys.exit(1)

    run_ingestion(args.source_dir, settings)


if __name__ == "__main__":
    main()
