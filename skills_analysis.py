import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


def load_skill_data(skill_file: Path) -> pd.DataFrame:
    """Load skill CSV and return DataFrame with Expression Name."""
    df = pd.read_csv(skill_file)
    if 'Expression Name' not in df.columns:
        raise ValueError(f"Expected column 'Expression Name' in {skill_file}")
    return df[['Expression Name']].dropna().rename(columns={'Expression Name': 'name'})


def load_count_data(count_file: Path) -> pd.DataFrame:
    """Load parent count CSV and return DataFrame with name and count."""
    df = pd.read_csv(count_file)
    if not {'name', 'count'}.issubset(df.columns):
        raise ValueError(f"Expected columns 'name' and 'count' in {count_file}")
    return df[['name', 'count']]


def merge_counts(exp_df: pd.DataFrame, count_df: pd.DataFrame) -> pd.DataFrame:
    """Merge expression data with counts."""
    return exp_df.merge(count_df, on='name', how='left')


def compute_deltas(df_2023: pd.DataFrame, df_2025: pd.DataFrame) -> pd.DataFrame:
    """Combine counts for 2023 and 2025 and compute differences."""
    df = pd.merge(df_2023, df_2025, on='name', how='outer', suffixes=('_2023', '_2025'))
    df.fillna(0, inplace=True)
    df['delta'] = df['count_2025'] - df['count_2023']
    return df


def plot_counts(df_2023: pd.DataFrame, df_2025: pd.DataFrame, output_dir: Path) -> None:
    """Plot total counts and top skills."""
    output_dir.mkdir(exist_ok=True, parents=True)
    # total count comparison
    total_counts = pd.DataFrame({
        'year': [2023, 2025],
        'total': [df_2023['count'].sum(), df_2025['count'].sum()],
    })
    sns.barplot(data=total_counts, x='year', y='total')
    plt.title('Total skill mentions by year')
    plt.tight_layout()
    plt.savefig(output_dir / 'total_counts.png')
    plt.close()

    # top 10 skills per year
    def plot_top(df, year):
        top = df.nlargest(10, 'count')
        sns.barplot(data=top, y='name', x='count')
        plt.title(f'Top 10 skills in {year}')
        plt.tight_layout()
        plt.savefig(output_dir / f'top_{year}.png')
        plt.close()

    plot_top(df_2023, 2023)
    plot_top(df_2025, 2025)

    # delta chart
    delta = compute_deltas(df_2023, df_2025).sort_values('delta', ascending=False).head(10)
    sns.barplot(data=delta, y='name', x='delta')
    plt.title('Top skill increases 2023 -> 2025')
    plt.tight_layout()
    plt.savefig(output_dir / 'delta_top.png')
    plt.close()

    # lost skills
    lost = delta.nsmallest(10, 'delta')
    sns.barplot(data=lost, y='name', x='delta')
    plt.title('Biggest skill decreases 2023 -> 2025')
    plt.tight_layout()
    plt.savefig(output_dir / 'delta_bottom.png')
    plt.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze skill CSV data")
    parser.add_argument("--skills_2023", default="skills_2023.csv", help="Path to skills 2023 CSV")
    parser.add_argument("--skills_2025", default="skills_2025.csv", help="Path to skills 2025 CSV")
    parser.add_argument("--counts_2023", default="2023.csv", help="Path to counts 2023 CSV")
    parser.add_argument("--counts_2025", default="2025.csv", help="Path to counts 2025 CSV")
    parser.add_argument("--output", default="charts", help="Directory to save charts")
    args = parser.parse_args()

    skills_2023 = load_skill_data(Path(args.skills_2023))
    skills_2025 = load_skill_data(Path(args.skills_2025))
    counts_2023 = merge_counts(skills_2023, load_count_data(Path(args.counts_2023)))
    counts_2025 = merge_counts(skills_2025, load_count_data(Path(args.counts_2025)))

    plot_counts(counts_2023, counts_2025, Path(args.output))
    print(f"Charts saved to {args.output}")
