# sandbox
sandbox

## `skills_analysis.py`

This script compares skill counts across two years and generates charts and CSV
summaries. Example usage:

```bash
python skills_analysis.py \
  --skills_2023 skills_2023.csv \
  --skills_2025 skills_2025.csv \
  --counts_2023 2023.csv \
  --counts_2025 2025.csv \
  --output charts
```

Optionally provide `--similarity_mapping` with a JSON file mapping skill names
to canonical forms. The script produces several charts (top skills, growth,
volatility, cumulative coverage) and writes CSV summaries of the delta between
years along with lists of new and disappeared skills.
