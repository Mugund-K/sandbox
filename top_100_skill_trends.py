import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

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


def get_common_top_skills(
    counts_2023: pd.DataFrame, counts_2025: pd.DataFrame, top_n: int = DEFAULT_TOP_N
) -> pd.DataFrame:
    """Return the top ``top_n`` skills appearing in both years with trend data."""
    merged = pd.merge(
        counts_2023,
        counts_2025,
        on="name",
        how="inner",
        suffixes=("_2023", "_2025"),
    )
    merged["total"] = merged["count_2023"] + merged["count_2025"]
    top = merged.sort_values("total", ascending=False).head(top_n)
    # Calculate percentage change from 2023 to 2025.  ``pd.NA`` avoids
    # divide-by-zero warnings when a skill has zero mentions in 2023.
    base = top["count_2023"].replace(0, pd.NA)
    top["pct_change"] = ((top["count_2025"] - top["count_2023"]) / base) * 100
    return top.drop(columns="total")


def plot_skill_trends(df: pd.DataFrame, output: Path) -> None:
    """Plot a grid of trend graphs for the provided skills."""
    n = len(df)
    rows = cols = int(n ** 0.5)
    if rows * cols < n:
        cols += 1
    if rows * cols < n:
        rows += 1

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 2, rows * 2), sharey=True)
    axes = axes.flatten()
    years = [2023, 2025]

    for ax, (_, row) in zip(axes, df.iterrows()):
        ax.plot(years, [row["count_2023"], row["count_2025"]], marker="o")
        ax.set_title(row["name"], fontsize=8)
        ax.set_xticks(years)

    # Hide any unused subplots
    for ax in axes[len(df) :]:
        ax.axis("off")

    fig.suptitle("Top common skill trends")
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot trend graphs for top common skills in 2023 and 2025"
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

    top_common = get_common_top_skills(counts_2023, counts_2025, args.top_n)

    # Round percentage change and add a trailing percent sign for the CSV
    csv_df = top_common.copy()
    csv_df["count_2023"] = csv_df["count_2023"].round().astype("Int64")
    csv_df["count_2025"] = csv_df["count_2025"].round().astype("Int64")
    csv_df["pct_change"] = (
        csv_df["pct_change"].round().astype("Int64").map(
            lambda x: f"{x}%" if pd.notna(x) else ""
        )
    )
    csv_df.to_csv(output_dir / "top_common_skills.csv", index=False)

    plot_skill_trends(top_common, output_dir / "skill_trends.png")
    print(f"Report written to {output_dir}")


if __name__ == "__main__":
    main()
