# sandbox
sandbox

## `skills_analysis.py`

This script compares skill counts across two years and generates charts and CSV summaries. Example usage:

```bash
python skills_analysis.py \
  --skills_2023 2023.csv \
  --skills_2025 2025.csv \
  --counts_2023 counts_2023.csv \
  --counts_2025 counts_2025.csv \
  --output charts
```

The files passed via `--skills_2023` and `--skills_2025` may either contain a column named `Expression Name` (the original export format) or a column named `processed_name` as in the `2023.csv`/`2025.csv` examples above.

Optionally provide `--similarity_mapping` with a JSON file mapping skill names to canonical forms. The script produces several charts (top skills, growth, volatility, cumulative coverage) and writes CSV summaries of the delta between years along with lists of new and disappeared skills.

## `top_100_skill_trends.py`

Generates a trend report for the skills that appear in both 2023 and 2025. The script takes the counts for each year, selects the top N shared skills (default 100) based on combined mentions, and produces a grid of line charts showing the change for each skill between the two years. A CSV with the selected skills is also written. In this CSV the ``pct_change`` column expresses the percentage increase or decrease from 2023 to 2025 for each skill. If the provided CSV lacks a `count` column the script looks for a file named `parent_<year>.csv` in the same directory, mirroring the structure of the public dataset.

Example:

```bash
python top_100_skill_trends.py \
  --counts_2023 2023.csv \
  --counts_2025 2025.csv \
  --output_dir trends
```

## `top_100_new_skills.py`

Lists the skills that are present in 2025 but absent in 2023. The script reads the count CSVs for both years and outputs the top N new skills ordered by their 2025 mention count.

```bash
python top_100_new_skills.py \
  --counts_2023 2023.csv \
  --counts_2025 2025.csv \
  --output_dir trends
```

The resulting CSV ``top_new_skills.csv`` contains the skill name and its count in 2025.

## `top_100_gone_skills.py`

Performs the inverse operation of ``top_100_new_skills.py``. It selects the skills that appear in 2023 but not in 2025 and writes the top N by 2023 mention count to ``top_gone_skills.csv``.

```bash
python top_100_gone_skills.py \
  --counts_2023 2023.csv \
  --counts_2025 2025.csv \
  --output_dir trends
```

## `top_100_volatile_skills.py`

Identifies the skills with the biggest percentage swings from 2023 to 2025. The script computes a volatility score as the absolute percentage change and lists the top N most volatile skills that appear in both years.

```bash
python top_100_volatile_skills.py \
  --counts_2023 2023.csv \
  --counts_2025 2025.csv \
  --output_dir trends
```

The resulting CSV `top_volatile_skills.csv` contains the skill name along with its volatility percentage and raw percent change.

## `top_100_growth_buckets.py`

Buckets skills into groups based on their percentage growth from 2023 to 2025 and writes the top skills from each group.

```bash
python top_100_growth_buckets.py \
  --counts_2023 2023.csv \
  --counts_2025 2025.csv \
  --output_dir trends
```

Four CSVs are produced in the output directory:
`top_high_growth_skills.csv`, `top_moderate_growth_skills.csv`,
`top_flat_skills.csv`, and `top_decline_skills.csv`.
