import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, Optional


def _read_csv_safely(path: Path, **kwargs) -> pd.DataFrame:
    """Read a CSV file and gracefully handle parsing errors."""
    try:
        return pd.read_csv(path, **kwargs)
    except pd.errors.ParserError as e:
        # Inform the user and retry using a more permissive configuration that
        # skips malformed lines.  ``on_bad_lines`` was introduced in pandas 1.3
        # while ``error_bad_lines`` is used in older versions.  Using the Python
        # engine avoids C-engine tokenization failures.
        print(
            f"Warning while reading {path}: {e}. "
            "Attempting to skip malformed lines with the Python engine."
        )
        try:
            return pd.read_csv(path, on_bad_lines="skip", engine="python", **kwargs)
        except TypeError:
            # Fallback for older pandas versions
            return pd.read_csv(
                path,
                error_bad_lines=False,
                warn_bad_lines=True,
                engine="python",
                **kwargs,
            )


def load_skill_data(skill_file: Path) -> pd.DataFrame:
    """Load a skill CSV and return a DataFrame with a ``name`` column."""
    df = _read_csv_safely(skill_file)

    # ``skills_2023.csv`` originally contained a column called ``Expression Name``.
    # Newer datasets may provide ``processed_name`` instead.  Support either
    # layout so callers can simply point ``--skills_2023``/``--skills_2025`` to
    # the appropriate file without additional preprocessing.
    if "Expression Name" in df.columns:
        column = "Expression Name"
    elif "processed_name" in df.columns:
        column = "processed_name"
    else:
        raise ValueError(
            f"Expected column 'Expression Name' or 'processed_name' in {skill_file}"
        )

    return df[[column]].dropna().rename(columns={column: "name"})


def load_count_data(count_file: Path) -> pd.DataFrame:
    """Load parent count CSV and return DataFrame with name and count."""
    df = _read_csv_safely(count_file)
    if not {'name', 'count'}.issubset(df.columns):
        raise ValueError(f"Expected columns 'name' and 'count' in {count_file}")
    return df[['name', 'count']]


def merge_counts(exp_df: pd.DataFrame, count_df: pd.DataFrame) -> pd.DataFrame:
    """Merge expression data with counts."""
    return exp_df.merge(count_df, on='name', how='left')


def compute_deltas(df_2023: pd.DataFrame, df_2025: pd.DataFrame) -> pd.DataFrame:
    """Combine counts for 2023 and 2025 and compute differences."""
    df = pd.merge(
        df_2023,
        df_2025,
        on="name",
        how="outer",
        suffixes=("_2023", "_2025"),
    )
    df.fillna(0, inplace=True)
    df["delta"] = df["count_2025"] - df["count_2023"]
    # Avoid divide-by-zero errors when computing percentage change
    base = df["count_2023"].replace(0, pd.NA)
    df["pct_change"] = (df["delta"] / base) * 100
    df["volatility"] = df["pct_change"].abs()

    def _bucket(pct: Optional[float]) -> str:
        if pd.isna(pct):
            return "New in 2025"
        if pct > 50:
            return "High growth (>50%)"
        if pct > 10:
            return "Moderate growth (10-50%)"
        if pct >= -10:
            return "Flat (\u00b110%)"
        return "Decline (>10% decrease)"

    df["growth_bucket"] = df["pct_change"].apply(_bucket)
    return df


def find_new_and_disappeared(delta_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Return DataFrames for new and disappeared skills."""
    new_skills = delta_df[delta_df["count_2023"] == 0].copy()
    disappeared = delta_df[delta_df["count_2025"] == 0].copy()
    return {"new": new_skills, "disappeared": disappeared}


def compute_cumulative_coverage(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate cumulative percentage coverage by rank."""
    df_sorted = df.sort_values("count", ascending=False).reset_index(drop=True)
    df_sorted["rank"] = range(1, len(df_sorted) + 1)
    total = df_sorted["count"].sum()
    df_sorted["cum_pct"] = df_sorted["count"].cumsum() / total * 100
    return df_sorted


def apply_similarity_mapping(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """Aggregate counts using a similarity mapping."""
    if not mapping:
        return df
    df = df.copy()
    df["_canonical"] = df["name"].map(mapping).fillna(df["name"])
    grouped = df.groupby("_canonical", as_index=False)["count"].sum()
    grouped.rename(columns={"_canonical": "name"}, inplace=True)
    return grouped


def plot_counts(df_2023: pd.DataFrame, df_2025: pd.DataFrame, output_dir: Path) -> None:
    """Plot total counts and various comparative charts."""
    output_dir.mkdir(exist_ok=True, parents=True)

    delta_df = compute_deltas(df_2023, df_2025)

    # total count comparison
    total_counts = pd.DataFrame(
        {
            "year": [2023, 2025],
            "total": [df_2023["count"].sum(), df_2025["count"].sum()],
        }
    )
    sns.barplot(data=total_counts, x="year", y="total")
    plt.title("Total skill mentions by year")
    plt.tight_layout()
    plt.savefig(output_dir / "total_counts.png")
    plt.close()

    # top 10 skills per year
    def plot_top(df: pd.DataFrame, year: int) -> None:
        top = df.nlargest(10, "count")
        sns.barplot(data=top, y="name", x="count")
        plt.title(f"Top 10 skills in {year}")
        plt.tight_layout()
        plt.savefig(output_dir / f"top_{year}.png")
        plt.close()

    plot_top(df_2023, 2023)
    plot_top(df_2025, 2025)

    # Top increases and decreases
    top_increase = delta_df.sort_values("delta", ascending=False).head(10)
    sns.barplot(data=top_increase, y="name", x="delta")
    plt.title("Top skill increases 2023 -> 2025")
    plt.tight_layout()
    plt.savefig(output_dir / "delta_top.png")
    plt.close()

    top_decrease = delta_df.sort_values("delta").head(10)
    sns.barplot(data=top_decrease, y="name", x="delta")
    plt.title("Biggest skill decreases 2023 -> 2025")
    plt.tight_layout()
    plt.savefig(output_dir / "delta_bottom.png")
    plt.close()

    # Most volatile skills
    volatile = delta_df.sort_values("volatility", ascending=False).head(10)
    sns.barplot(data=volatile, y="name", x="volatility")
    plt.title("Most volatile skills")
    plt.tight_layout()
    plt.savefig(output_dir / "volatile_top.png")
    plt.close()

    # cumulative coverage charts
    for year, df in [(2023, df_2023), (2025, df_2025)]:
        cov = compute_cumulative_coverage(df)
        sns.lineplot(data=cov, x="rank", y="cum_pct")
        plt.title(f"Cumulative coverage {year}")
        plt.ylabel("Cumulative % of mentions")
        plt.xlabel("Skill rank")
        plt.ylim(0, 100)
        plt.tight_layout()
        plt.savefig(output_dir / f"coverage_{year}.png")
        plt.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze skill CSV data")
    parser.add_argument("--skills_2023", default="skills_2023.csv", help="Path to skills 2023 CSV")
    parser.add_argument("--skills_2025", default="skills_2025.csv", help="Path to skills 2025 CSV")
    parser.add_argument("--counts_2023", default="2023.csv", help="Path to counts 2023 CSV")
    parser.add_argument("--counts_2025", default="2025.csv", help="Path to counts 2025 CSV")
    parser.add_argument("--output", default="charts", help="Directory to save charts")
    parser.add_argument(
        "--similarity_mapping",
        default=None,
        help="Optional JSON file mapping skills to canonical names",
    )
    args = parser.parse_args()

    skills_2023 = load_skill_data(Path(args.skills_2023))
    skills_2025 = load_skill_data(Path(args.skills_2025))
    counts_2023 = merge_counts(
        skills_2023, load_count_data(Path(args.counts_2023))
    )
    counts_2025 = merge_counts(
        skills_2025, load_count_data(Path(args.counts_2025))
    )

    mapping: Dict[str, str] = {}
    if args.similarity_mapping:
        mapping = pd.read_json(Path(args.similarity_mapping), typ="series").to_dict()
        counts_2023 = apply_similarity_mapping(counts_2023, mapping)
        counts_2025 = apply_similarity_mapping(counts_2025, mapping)

    plot_counts(counts_2023, counts_2025, Path(args.output))

    delta_df = compute_deltas(counts_2023, counts_2025)
    delta_df.to_csv(Path(args.output) / "delta_summary.csv", index=False)

    new_old = find_new_and_disappeared(delta_df)
    new_old["new"].to_csv(Path(args.output) / "new_skills.csv", index=False)
    new_old["disappeared"].to_csv(Path(args.output) / "disappeared_skills.csv", index=False)

    print(f"Charts and summaries saved to {args.output}")
