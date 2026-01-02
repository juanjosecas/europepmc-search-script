# Example Workflows

This document provides practical examples of how to use the European PMC search script and NLP analysis tools together.

## Workflow 1: Quick Exploration

Before downloading large amounts of data, explore what's available:

```bash
# Get statistics for a broad search
python epmc.py "cancer treatment" csv --stats

# Get statistics for a more specific search with filters
python epmc.py "immunotherapy" csv --stats --start_year 2018 --end_year 2023 --open_access Y
```

## Workflow 2: Download and Analyze Recent Research

Search for recent research with full details, then analyze:

```bash
# Step 1: Download articles with abstracts
python epmc.py "machine learning healthcare" csv --start_year 2020 --end_year 2023 \
  --open_access Y --include_extra --result_type core --max_results 500

# Step 2: Perform comprehensive NLP analysis
python nlp_analysis.py records.csv --all
```

## Workflow 3: Topic Discovery

Find emerging topics in a research area:

```bash
# Step 1: Download articles with abstracts
python epmc.py "CRISPR gene editing" csv --start_year 2019 --end_year 2023 \
  --include_extra --sort date --max_results 1000

# Step 2: Perform topic modeling
python nlp_analysis.py records.csv --abstract_analysis --topics 10
```

## Workflow 4: Journal Analysis

Find out which journals publish most on your topic:

```bash
# Step 1: Get statistics with journal distribution
python epmc.py "quantum computing" csv --stats --start_year 2015 --end_year 2023

# Step 2: Download full results for further analysis
python epmc.py "quantum computing" csv --start_year 2015 --end_year 2023 --max_results 2000
```

## Workflow 5: Trend Analysis Over Time

Analyze how research topics have evolved:

```bash
# Step 1: Download articles across multiple years
python epmc.py "artificial intelligence" csv --start_year 2010 --end_year 2023 \
  --max_results 5000

# Step 2: Analyze publication trends
python nlp_analysis.py records.csv --trends

# Step 3: Analyze keyword evolution
python nlp_analysis.py records.csv --title_analysis --top_words 30 --wordcloud
```

## Workflow 6: Finding Highly Cited Papers

Download and sort by citation count:

```bash
# Download articles sorted by citation count
python epmc.py "deep learning" csv --sort cited --max_results 1000 \
  --start_year 2015 --end_year 2023

# Get statistics to see citation distribution
python epmc.py "deep learning" csv --stats --sort cited
```

## Workflow 7: Robust Download for Large Datasets

When downloading large datasets with potentially unstable connections:

```bash
# Use increased timeout and retries for stability
python epmc.py "covid-19" csv --timeout 60 --retries 5 \
  --page_size 1000 --max_results 10000 --include_extra
```

## Workflow 8: Multi-format Analysis

Export to different formats for different uses:

```bash
# Export to CSV for Python/R analysis
python epmc.py "bioinformatics" csv --max_results 1000

# Export to Excel for easy viewing and sharing
python epmc.py "bioinformatics" excel --max_results 1000

# Export to JSON for web applications
python epmc.py "bioinformatics" json --max_results 1000
```

## Workflow 9: Synonym Expansion for Comprehensive Searches

Use synonym expansion to catch related terms:

```bash
# Search with synonyms enabled
python epmc.py "heart disease" csv --synonym true --start_year 2018 \
  --end_year 2023 --max_results 2000

# Compare with synonym disabled to see the difference
python epmc.py "heart disease" csv --synonym false --stats
```

## Workflow 10: Language-Specific Research

Focus on research in specific languages:

```bash
# English research only
python epmc.py "neuroscience" csv --lang eng --max_results 1000

# Compare across time periods
python epmc.py "neuroscience" csv --lang eng --start_year 2015 --end_year 2018 --stats
python epmc.py "neuroscience" csv --lang eng --start_year 2019 --end_year 2023 --stats
```

## Tips for Efficient Workflows

1. **Always start with --stats** to understand the data volume before downloading
2. **Use --max_results** to limit large downloads and avoid overwhelming your system
3. **Enable --include_extra only when needed** for NLP analysis (abstracts required)
4. **Adjust --timeout and --retries** based on your network conditions
5. **Use --result_type core** only when you need complete article metadata
6. **Sort strategically**: Use `--sort date` for recent work, `--sort cited` for influential papers
7. **Clean up output files** between runs to avoid mixing results from different searches

## Troubleshooting

### Connection Issues
If you experience frequent connection failures:
```bash
python epmc.py "query" csv --timeout 60 --retries 5
```

### Memory Issues with Large Datasets
Break down large downloads:
```bash
# Year by year
python epmc.py "query" csv --start_year 2020 --end_year 2020 --max_results 5000
python epmc.py "query" csv --start_year 2021 --end_year 2021 --max_results 5000
```

### NLP Analysis Dependencies Missing
Install visualization tools for enhanced analysis:
```bash
pip install wordcloud matplotlib
```

## Advanced: Combining with Other Tools

### Export to R for Statistical Analysis
```bash
python epmc.py "clinical trial" csv --max_results 5000
# Then in R: data <- read.csv("records.csv")
```

### Export to Tableau/Power BI
```bash
python epmc.py "epidemiology" excel --max_results 10000
# Import the Excel file into your BI tool
```

### Pipeline with Shell Scripts
```bash
#!/bin/bash
# search_and_analyze.sh
python epmc.py "$1" csv --include_extra --max_results 1000
python nlp_analysis.py records.csv --all
```
