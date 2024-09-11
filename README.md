# European PMC Search Script

This Python script automates the process of searching for scientific articles in the European PMC database using its RESTful API. It allows users to query the database with multiple filters (e.g., publication year, article type, open access, language) and handles large datasets by managing pagination and errors. The script can export the retrieved data in CSV, JSON, or Excel format.

## Features

- **Advanced Search**: Customize queries with filters such as publication year range, article type, language, and open access.
- **Efficient Data Handling**: Manages large datasets through pagination and handles rate limiting or connection issues.
- **Export Formats**: Outputs data in CSV, JSON, or Excel format, depending on user preference.
- **Customizable**: Allows additional information to be included in the output (such as abstracts and full text links).
- **Logging**: Logs all actions, errors, and responses for debugging and performance monitoring.

## Requirements

To use the script, you need to have the following Python packages installed:

```bash
pip install requests pandas argparse openpyxl
```

## Usage

You can run the script directly from the command line with the following arguments:

### Basic Usage

```bash
python script.py <query_term> <output_format> [--start_year <year>] [--end_year <year>] [--article_type <type>] [--open_access <Y/N>] [--lang <language>] [--include_extra]
```

### Example

Search for articles related to "machine learning" published between 2015 and 2020, available in open access and written in English:

```bash
python script.py "machine learning" csv --start_year 2015 --end_year 2020 --open_access Y --lang eng
```

### Arguments

- **query_term**: The main search term, e.g., `"cancer"`, `"machine learning"`.
- **output_format**: The format for exporting results (`csv`, `json`, `excel`).
- **--start_year**: The start year for filtering articles (optional).
- **--end_year**: The end year for filtering articles (optional).
- **--article_type**: The type of articles to search for, e.g., `"research-article"`, `"review"` (optional).
- **--open_access**: Filter by open access articles (`Y` for yes, `N` for no) (optional).
- **--lang**: Filter by language, e.g., `"eng"` for English (optional).
- **--include_extra**: Include additional information in the output (abstract, full text link) (optional).

## How It Works

1. **Preprocessing**: The search query is normalized (lowercased and trimmed) and validated.
2. **API Request**: The script sends the search request to the European PMC API with pagination support, fetching 1000 records at a time.
3. **Data Extraction**: The relevant data (e.g., title, authors, journal, DOI) is extracted from the API response.
4. **Error Handling**: If the API rate limit is exceeded, the script waits and retries automatically.
5. **Exporting Data**: The results are saved to a file in the chosen format (CSV, JSON, Excel).

## Example Output

Here is an example of how the output might look in CSV format:

| Title | Author | Journal | Year | DOI | Open Access |
|-------|--------|---------|------|-----|-------------|
| Machine Learning in Cancer Research | John Doe | Nature | 2020 | 10.1234/nature12345 | Y |
| Deep Learning for Medical Imaging | Jane Smith | Science | 2019 | 10.1234/science67890 | N |

## Logging

All events, including errors, are logged in `search_log.log`. This includes API requests, pagination, retries, and any issues encountered during the process.

## Contributing

Feel free to fork the repository and submit pull requests for improvements or additional features. Make sure your contributions are well-documented and tested.

## License

This project is licensed under the MIT License.
