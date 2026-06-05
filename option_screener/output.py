"""Output writers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_excel(df: pd.DataFrame, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False)
    return output_path
