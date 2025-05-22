import argparse
from pathlib import Path

import pandas as pd

from skills_analysis import _read_csv_safely


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


def get_new_skills(
    counts_2023: pd.DataFrame, counts_2025: pd.DataFrame, top_n: int = DEFAULT_TOP_N
) -> pd.DataFrame:
    """Return the top ``top_n`` skills that appear in 2025 but not in 2023."""
    c2025 = counts_2025.rename(columns={"count": "count_2025"})
    new = c2025[~c2025["name"].isin(counts_2023["name"])]
    return new.sort_values("count_2025", ascending=False).head(top_n)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List the top new skills that appear in 2025 but not 2023"
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

    new_skills = get_new_skills(counts_2023, counts_2025, args.top_n)
    new_skills.to_csv(output_dir / "top_new_skills.csv", index=False)

    print(f"Report written to {output_dir}")


if __name__ == "__main__":
    main()
