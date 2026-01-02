# European PMC Search Script

This Python script automates the process of searching for scientific articles in the European PMC database using its RESTful API. It allows users to query the database with multiple filters (e.g., publication year, article type, open access, language) and handles large datasets by managing pagination and errors. The script can export the retrieved data in CSV, JSON, or Excel format.

## Features

- **Advanced Search**: Customize queries with filters such as publication year range, article type, language, and open access.
- **Efficient Data Handling**: Manages large datasets through pagination and handles rate limiting or connection issues.
- **Robust Error Handling**: Implements exponential backoff, timeout handling, and comprehensive error recovery mechanisms.
- **Export Formats**: Outputs data in CSV, JSON, or Excel format, depending on user preference.
- **Quick Statistics**: Get instant statistics about search results without downloading all data.
- **Customizable**: Allows additional information to be included in the output (such as abstracts and full text links).
- **NLP Analysis**: Separate script for performing Natural Language Processing analysis on search results.
- **Logging**: Logs all actions, errors, and responses for debugging and performance monitoring.

## Requirements

To use the script, you need to have the following Python packages installed:

### Basic Requirements (for epmc.py)
```bash
pip install requests pandas openpyxl
```

### NLP Analysis Requirements (for nlp_analysis.py)
```bash
pip install pandas nltk wordcloud matplotlib scikit-learn
```

## Usage

### Search Script (epmc.py)

You can run the script directly from the command line with the following arguments:

#### Basic Usage

```bash
python epmc.py <query_term> <output_format> [options]
```

#### Examples

Search for articles related to "machine learning" published between 2015 and 2020, available in open access and written in English:

```bash
python epmc.py "machine learning" csv --start_year 2015 --end_year 2020 --open_access Y --lang eng
```

Get quick statistics without downloading all data:

```bash
python epmc.py "cancer" csv --stats
```

Search with custom page size and sort by date:

```bash
python epmc.py "covid-19" json --page_size 500 --sort date --max_results 5000
```

Search with synonym expansion and extra fields:

```bash
python epmc.py "diabetes" csv --synonym true --include_extra --result_type core
```

#### Arguments

**Positional Arguments:**
- **query_term**: The main search term, e.g., `"cancer"`, `"machine learning"`.
- **output_format**: The format for exporting results (`csv`, `json`, `excel`).

**Optional Arguments:**
- **--start_year**: The start year for filtering articles (e.g., 2010).
- **--end_year**: The end year for filtering articles (e.g., 2021).
- **--article_type**: The type of articles to search for, e.g., `"research-article"`, `"review"`.
- **--open_access**: Filter by open access articles (`Y` for yes, `N` for no).
- **--lang**: Filter by language, e.g., `"eng"` for English.
- **--include_extra**: Include additional information in the output (abstract, full text link).
- **--page_size**: Number of results per page (default: 1000, max: 1000).
- **--sort**: Sort results by `relevance`, `date`, or `cited`.
- **--result_type**: Result type: `lite` (basic fields) or `core` (full details).
- **--synonym**: Enable synonym expansion in search (`true`/`false`).
- **--max_results**: Maximum number of results to retrieve.
- **--timeout**: Request timeout in seconds (default: 30).
- **--retries**: Number of retry attempts for failed requests (default: 3).
- **--stats**: Display quick statistics instead of downloading all data.

### NLP Analysis Script (nlp_analysis.py)

After collecting data with `epmc.py`, you can analyze it using the NLP analysis script.

#### Basic Usage

```bash
python nlp_analysis.py <input_file> [options]
```

#### Examples

Perform all available analyses:

```bash
python nlp_analysis.py records.csv --all
```

Analyze word frequency in titles:

```bash
python nlp_analysis.py records.csv --title_analysis --top_words 30
```

Extract keywords from abstracts and perform topic modeling:

```bash
python nlp_analysis.py records.csv --abstract_analysis --topics 10
```

Generate word cloud and analyze publication trends:

```bash
python nlp_analysis.py records.csv --title_analysis --wordcloud --trends
```

#### Arguments

**Positional Arguments:**
- **input_file**: Input file with search results (CSV, JSON, or Excel).

**Optional Arguments:**
- **--format**: Input file format (`csv`, `json`, `excel`). Default: csv.
- **--title_analysis**: Perform word frequency analysis on titles.
- **--abstract_analysis**: Perform keyword extraction on abstracts (requires --include_extra during search).
- **--topics**: Number of topics for topic modeling (default: 5).
- **--top_words**: Number of top words to display (default: 20).
- **--wordcloud**: Generate word cloud visualization.
- **--trends**: Analyze publication trends over time.
- **--all**: Perform all available analyses.

## How It Works

### Search Script (epmc.py)

1. **Preprocessing**: The search query is normalized (lowercased and trimmed) and validated.
2. **API Request**: The script sends the search request to the European PMC API with pagination support, fetching up to 1000 records at a time.
3. **Data Extraction**: The relevant data (e.g., title, authors, journal, DOI) is extracted from the API response.
4. **Error Handling**: 
   - Implements exponential backoff for retries
   - Handles connection timeouts
   - Manages rate limiting (429 errors)
   - Validates API responses
   - Recovers from server errors (5xx)
5. **Exporting Data**: The results are saved to a file in the chosen format (CSV, JSON, Excel).

### NLP Analysis Script (nlp_analysis.py)

1. **Data Loading**: Loads search results from CSV, JSON, or Excel files.
2. **Text Preprocessing**: Tokenizes text, removes stopwords, and filters out non-alphabetic tokens.
3. **Analysis**:
   - **Word Frequency**: Counts and ranks the most common words in titles or abstracts.
   - **TF-IDF Keyword Extraction**: Identifies the most important terms using TF-IDF scoring.
   - **Topic Modeling**: Discovers latent topics using Latent Dirichlet Allocation (LDA).
   - **Visualization**: Generates word clouds and publication trend charts.
4. **Output**: Displays results in the console and saves visualizations as image files.

## Example Output

### Search Results (CSV format)

| Title | Author | Journal | Year | DOI | Open Access |
|-------|--------|---------|------|-----|-------------|
| Machine Learning in Cancer Research | John Doe | Nature | 2020 | 10.1234/nature12345 | Y |
| Deep Learning for Medical Imaging | Jane Smith | Science | 2019 | 10.1234/science67890 | N |

### Quick Statistics Output

```
============================================================
QUICK STATISTICS
============================================================

Total Results: 1523

--- Year Distribution (Top 10) ---
  2020: 245 (16.1%)
  2019: 312 (20.5%)
  2018: 198 (13.0%)
  ...

--- Open Access Statistics ---
  Y: 892 (58.6%)
  N: 631 (41.4%)

--- Top 10 Journals ---
  Nature: 87 (5.7%)
  Science: 64 (4.2%)
  ...

--- Citation Statistics ---
  Average citations: 23.4
  Maximum citations: 456
  Total citations: 35632
============================================================
```

### NLP Analysis Output

```
============================================================
WORD FREQUENCY ANALYSIS - TITLE
============================================================

Total unique words: 1245
Total words: 8937

Top 20 most common words:
  machine              : 234
  learning             : 198
  analysis             : 156
  ...

============================================================
KEYWORD EXTRACTION (TF-IDF) - ABSTRACT
============================================================

Top 20 keywords by TF-IDF score:
  algorithm            : 0.3456
  neural               : 0.3201
  prediction           : 0.2987
  ...

============================================================
TOPIC MODELING (LDA) - ABSTRACT
============================================================

Discovered 5 topics:

Topic 1: neural, network, deep, learning, model
Topic 2: cancer, treatment, patient, clinical, therapy
Topic 3: gene, expression, protein, cell, molecular
...
```

## Logging

All events, including errors, are logged in `search_log.log` (for epmc.py) and `nlp_analysis.log` (for nlp_analysis.py). This includes API requests, pagination, retries, and any issues encountered during the process.

## Error Handling

The script includes comprehensive error handling:

- **Connection Errors**: Automatic retry with exponential backoff (up to configurable number of attempts)
- **Timeouts**: Configurable timeout for API requests with retry logic
- **Rate Limiting**: Automatic detection and handling of API rate limits (429 errors)
- **Server Errors**: Retry logic for temporary server issues (5xx errors)
- **Invalid Responses**: Validation of API response structure before processing
- **File I/O Errors**: Proper error handling for file operations with informative messages

## Tips for Best Results

1. **Use the --stats flag first** to understand the volume of results before downloading
2. **Set --max_results** to limit downloads for large result sets
3. **Use --include_extra with --result_type core** to get full details including abstracts for NLP analysis
4. **For NLP analysis**, always collect data with `--include_extra` to get abstracts
5. **Adjust --timeout and --retries** based on your network conditions
6. **Use --synonym true** to expand your search with related terms

## Contributing

Feel free to fork the repository and submit pull requests for improvements or additional features. Make sure your contributions are well-documented and tested.

## License

This project is licensed under the MIT License.
