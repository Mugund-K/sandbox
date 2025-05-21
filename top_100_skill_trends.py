import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


DEFAULT_TOP_N = 100


def load_count_data(path: Path) -> pd.DataFrame:
    """Load a CSV containing columns ``name`` and ``count``."""
    df = pd.read_csv(path)
    if not {'name', 'count'}.issubset(df.columns):
        raise ValueError(f"Expected columns 'name' and 'count' in {path}")
    return df[['name', 'count']]


def get_common_top_skills(
    counts_2023: pd.DataFrame, counts_2025: pd.DataFrame, top_n: int = DEFAULT_TOP_N
) -> pd.DataFrame:
    """Return the top ``top_n`` skills appearing in both years."""
    merged = pd.merge(
        counts_2023,
        counts_2025,
        on="name",
        how="inner",
        suffixes=("_2023", "_2025"),
    )
    merged["total"] = merged["count_2023"] + merged["count_2025"]
    return merged.sort_values("total", ascending=False).head(top_n)


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
    top_common.to_csv(output_dir / "top_common_skills.csv", index=False)

    plot_skill_trends(top_common, output_dir / "skill_trends.png")
    print(f"Report written to {output_dir}")


if __name__ == "__main__":
    main()
