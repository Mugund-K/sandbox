import argparse
from pathlib import Path

import pandas as pd

from skills_analysis import _read_csv_safely, compute_deltas

DEFAULT_TOP_N = 100


def load_count_data(path: Path) -> pd.DataFrame:
    """Load a CSV containing columns ``name`` and ``count``.

    If ``path`` lacks the required columns, look for a file named
    ``parent_<original>`` in the same directory.  This mirrors the layout of the
    example dataset where aggregated counts live in ``parent_2023.csv`` and
    ``parent_2025.csv`` while ``2023.csv``/``2025.csv`` only contain raw skill
    rows.
    """
    df = _read_csv_safely(path)
    if not {"name", "count"}.issubset(df.columns):
        alt_path = path.with_name(f"parent_{path.name}")
        if alt_path.exists():
            df = _read_csv_safely(alt_path)
    if not {"name", "count"}.issubset(df.columns):
        raise ValueError(
            f"Expected columns 'name' and 'count' in {path} or {alt_path}"
        )
    return df[["name", "count"]]


def get_volatile_skills(
    counts_2023: pd.DataFrame, counts_2025: pd.DataFrame, top_n: int = DEFAULT_TOP_N
) -> pd.DataFrame:
    """Return the ``top_n`` most volatile skills shared between both years."""
    deltas = compute_deltas(counts_2023, counts_2025)
    shared = deltas.dropna(subset=["pct_change"])
    return shared.sort_values("volatility", ascending=False).head(top_n)[
        ["name", "volatility", "pct_change"]
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List the most volatile skills between 2023 and 2025"
    )
    parser.add_argument("--counts_2023", default="2023.csv", help="Counts for 2023")
    parser.add_argument("--counts_2025", default="2025.csv", help="Counts for 2025")
    parser.add_argument(
        "--output_dir", default="trends", help="Directory to write reports"
    )
    parser.add_argument(
        "--top_n", type=int, default=DEFAULT_TOP_N, help="Number of skills to include"
    )

    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    counts_2023 = load_count_data(Path(args.counts_2023))
    counts_2025 = load_count_data(Path(args.counts_2025))

    volatile = get_volatile_skills(counts_2023, counts_2025, args.top_n)
    volatile.to_csv(output_dir / "top_volatile_skills.csv", index=False)

    print(f"Report written to {output_dir}")


if __name__ == "__main__":
    main()
