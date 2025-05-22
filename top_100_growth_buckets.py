import argparse
from pathlib import Path

import pandas as pd

from skills_analysis import _read_csv_safely, compute_deltas

DEFAULT_TOP_N = 100


def load_count_data(path: Path) -> pd.DataFrame:
    """Load a CSV containing columns ``name`` and ``count``.

    If ``path`` lacks the required columns, look for a file named
    ``parent_<original>`` in the same directory. This mirrors the layout of the
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


def bucket_skills(
    counts_2023: pd.DataFrame, counts_2025: pd.DataFrame, top_n: int = DEFAULT_TOP_N
) -> dict[str, pd.DataFrame]:
    """Return ``top_n`` skills for each growth bucket."""
    deltas = compute_deltas(counts_2023, counts_2025)
    result: dict[str, pd.DataFrame] = {}

    order = [
        "High growth (>50%)",
        "Moderate growth (10-50%)",
        "Flat (±10%)",
        "Decline (>10% decrease)",
    ]

    for label in order:
        subset = deltas[deltas["growth_bucket"] == label].copy()
        if label == "Decline (>10% decrease)":
            subset = subset.sort_values("pct_change").head(top_n)
        else:
            subset = subset.sort_values("pct_change", ascending=False).head(top_n)
        result[label] = subset[["name", "pct_change", "count_2023", "count_2025"]]

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bucket skills by growth between 2023 and 2025"
    )
    parser.add_argument("--counts_2023", default="2023.csv", help="Counts for 2023")
    parser.add_argument("--counts_2025", default="2025.csv", help="Counts for 2025")
    parser.add_argument(
        "--output_dir", default="trends", help="Directory to write reports"
    )
    parser.add_argument(
        "--top_n", type=int, default=DEFAULT_TOP_N, help="Number of skills per bucket"
    )

    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    counts_2023 = load_count_data(Path(args.counts_2023))
    counts_2025 = load_count_data(Path(args.counts_2025))

    buckets = bucket_skills(counts_2023, counts_2025, args.top_n)

    file_map = {
        "High growth (>50%)": "top_high_growth_skills.csv",
        "Moderate growth (10-50%)": "top_moderate_growth_skills.csv",
        "Flat (±10%)": "top_flat_skills.csv",
        "Decline (>10% decrease)": "top_decline_skills.csv",
    }

    for label, df in buckets.items():
        df.to_csv(output_dir / file_map[label], index=False)

    print(f"Report written to {output_dir}")


if __name__ == "__main__":
    main()
