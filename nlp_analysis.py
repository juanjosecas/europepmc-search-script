#!/usr/bin/env python3
"""
NLP Analysis Script for European PMC Search Results

This script performs Natural Language Processing analysis on the results
obtained from the European PMC search script. It provides:
- Word frequency analysis on titles
- Keyword extraction from abstracts
- Topic modeling
- Visualization of results

Requirements:
    pip install pandas nltk wordcloud matplotlib scikit-learn
"""

import argparse
import json
import csv
import logging
from collections import Counter
import re
import sys

try:
    import pandas as pd
except ImportError:
    print("Error: pandas is not installed. Install it with: pip install pandas")
    sys.exit(1)

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
except ImportError:
    print("Error: nltk is not installed. Install it with: pip install nltk")
    sys.exit(1)

try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
except ImportError:
    print("Warning: wordcloud and/or matplotlib not installed. Visualizations will be disabled.")
    print("Install with: pip install wordcloud matplotlib")
    WordCloud = None
    plt = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
    from sklearn.decomposition import LatentDirichletAllocation
except ImportError:
    print("Warning: scikit-learn not installed. Topic modeling will be disabled.")
    print("Install with: pip install scikit-learn")
    TfidfVectorizer = None
    CountVectorizer = None
    LatentDirichletAllocation = None

# Configure logging
logging.basicConfig(filename='nlp_analysis.log', level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Download required NLTK data
def download_nltk_data():
    """Download required NLTK data packages."""
    try:
        nltk.data.find('tokenizers/punkt_tab')
        nltk.data.find('corpora/stopwords')
    except LookupError:
        print("Downloading required NLTK data...")
        try:
            nltk.download('punkt_tab', quiet=True)
        except:
            nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        print("NLTK data downloaded successfully.")

def load_data(file_path, file_format='csv'):
    """Load data from CSV, JSON, or Excel file."""
    try:
        if file_format == 'csv':
            df = pd.read_csv(file_path)
        elif file_format == 'json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        elif file_format == 'excel':
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
        
        logging.info(f"Loaded {len(df)} records from {file_path}")
        print(f"\nLoaded {len(df)} records from {file_path}")
        return df
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        print(f"Error: File not found: {file_path}")
        return None
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        print(f"Error loading data: {e}")
        return None

def preprocess_text(text, remove_stopwords=True):
    """Preprocess text by tokenizing and removing stopwords."""
    if pd.isna(text) or not isinstance(text, str):
        return []
    
    # Convert to lowercase and tokenize
    text = text.lower()
    tokens = word_tokenize(text)
    
    # Remove punctuation and non-alphabetic tokens
    tokens = [token for token in tokens if token.isalpha()]
    
    # Remove stopwords if requested
    if remove_stopwords:
        try:
            stop_words = set(stopwords.words('english'))
            tokens = [token for token in tokens if token not in stop_words and len(token) > 2]
        except:
            # If stopwords are not available, just filter short words
            tokens = [token for token in tokens if len(token) > 2]
    
    return tokens

def analyze_word_frequency(df, column='title', top_n=20):
    """Analyze word frequency in the specified column."""
    print(f"\n{'='*60}")
    print(f"WORD FREQUENCY ANALYSIS - {column.upper()}")
    print(f"{'='*60}\n")
    
    all_words = []
    for text in df[column].dropna():
        words = preprocess_text(text)
        all_words.extend(words)
    
    if not all_words:
        print("No words found for analysis.")
        return None
    
    word_freq = Counter(all_words)
    
    print(f"Total unique words: {len(word_freq)}")
    print(f"Total words: {sum(word_freq.values())}")
    print(f"\nTop {top_n} most common words:")
    
    for word, count in word_freq.most_common(top_n):
        print(f"  {word:20s}: {count:5d}")
    
    logging.info(f"Analyzed word frequency for {len(df)} {column}s")
    return word_freq

def extract_keywords_tfidf(df, column='abstract', top_n=20):
    """Extract keywords using TF-IDF."""
    if TfidfVectorizer is None:
        print("\nKeyword extraction requires scikit-learn. Please install it.")
        return None
    
    print(f"\n{'='*60}")
    print(f"KEYWORD EXTRACTION (TF-IDF) - {column.upper()}")
    print(f"{'='*60}\n")
    
    # Filter out missing values
    texts = df[column].dropna().tolist()
    
    if not texts:
        print(f"No {column} data available for keyword extraction.")
        return None
    
    # Preprocess texts
    processed_texts = [' '.join(preprocess_text(text)) for text in texts]
    
    # Remove empty texts
    processed_texts = [text for text in processed_texts if text.strip()]
    
    if not processed_texts:
        print("No valid text data after preprocessing.")
        return None
    
    try:
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(max_features=100, min_df=2, max_df=0.8)
        tfidf_matrix = vectorizer.fit_transform(processed_texts)
        
        # Get feature names and their average TF-IDF scores
        feature_names = vectorizer.get_feature_names_out()
        avg_tfidf = tfidf_matrix.mean(axis=0).A1
        
        # Create a list of (word, score) tuples and sort by score
        word_scores = list(zip(feature_names, avg_tfidf))
        word_scores.sort(key=lambda x: x[1], reverse=True)
        
        print(f"Top {top_n} keywords by TF-IDF score:")
        for word, score in word_scores[:top_n]:
            print(f"  {word:20s}: {score:.4f}")
        
        logging.info(f"Extracted keywords from {len(texts)} {column}s")
        return word_scores
    except Exception as e:
        logging.error(f"Error in TF-IDF extraction: {e}")
        print(f"Error in keyword extraction: {e}")
        return None

def perform_topic_modeling(df, column='abstract', n_topics=5, n_words=10):
    """Perform topic modeling using LDA."""
    if CountVectorizer is None or LatentDirichletAllocation is None:
        print("\nTopic modeling requires scikit-learn. Please install it.")
        return None
    
    print(f"\n{'='*60}")
    print(f"TOPIC MODELING (LDA) - {column.upper()}")
    print(f"{'='*60}\n")
    
    # Filter out missing values
    texts = df[column].dropna().tolist()
    
    if not texts:
        print(f"No {column} data available for topic modeling.")
        return None
    
    if len(texts) < n_topics:
        print(f"Not enough documents ({len(texts)}) for {n_topics} topics. Adjusting to {len(texts)} topics.")
        n_topics = max(1, len(texts) // 2)
    
    # Preprocess texts
    processed_texts = [' '.join(preprocess_text(text)) for text in texts]
    processed_texts = [text for text in processed_texts if text.strip()]
    
    if not processed_texts or len(processed_texts) < 2:
        print("Not enough valid text data for topic modeling.")
        return None
    
    try:
        # Create document-term matrix
        vectorizer = CountVectorizer(max_features=100, min_df=2, max_df=0.8)
        doc_term_matrix = vectorizer.fit_transform(processed_texts)
        
        # Perform LDA
        lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
        lda.fit(doc_term_matrix)
        
        # Get feature names
        feature_names = vectorizer.get_feature_names_out()
        
        # Display topics
        print(f"Discovered {n_topics} topics:\n")
        for topic_idx, topic in enumerate(lda.components_):
            top_words_idx = topic.argsort()[-n_words:][::-1]
            top_words = [feature_names[i] for i in top_words_idx]
            print(f"Topic {topic_idx + 1}: {', '.join(top_words)}")
        
        logging.info(f"Performed topic modeling on {len(texts)} {column}s")
        return lda, vectorizer
    except Exception as e:
        logging.error(f"Error in topic modeling: {e}")
        print(f"Error in topic modeling: {e}")
        return None

def generate_wordcloud(word_freq, output_file='wordcloud.png'):
    """Generate and save a word cloud visualization."""
    if WordCloud is None or plt is None:
        print("\nWord cloud generation requires wordcloud and matplotlib.")
        return
    
    try:
        # Create word cloud
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(word_freq)
        
        # Display and save
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('Word Cloud of Most Frequent Terms')
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\nWord cloud saved to: {output_file}")
        logging.info(f"Word cloud saved to {output_file}")
    except Exception as e:
        logging.error(f"Error generating word cloud: {e}")
        print(f"Error generating word cloud: {e}")

def analyze_publication_trends(df):
    """Analyze publication trends over time."""
    print(f"\n{'='*60}")
    print("PUBLICATION TRENDS")
    print(f"{'='*60}\n")
    
    if 'pubYear' not in df.columns:
        print("Publication year data not available.")
        return
    
    # Count publications by year
    year_counts = df['pubYear'].value_counts().sort_index()
    
    print("Publications by year:")
    for year, count in year_counts.items():
        print(f"  {year}: {count}")
    
    if plt is not None:
        try:
            plt.figure(figsize=(12, 6))
            year_counts.plot(kind='bar')
            plt.title('Publications by Year')
            plt.xlabel('Year')
            plt.ylabel('Number of Publications')
            plt.tight_layout()
            plt.savefig('publication_trends.png', dpi=300, bbox_inches='tight')
            print("\nPublication trends chart saved to: publication_trends.png")
            logging.info("Publication trends chart saved")
        except Exception as e:
            logging.error(f"Error generating publication trends chart: {e}")
            print(f"Error generating chart: {e}")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="NLP Analysis for European PMC Search Results")
    parser.add_argument('input_file', help='Input file (CSV, JSON, or Excel)')
    parser.add_argument('--format', choices=['csv', 'json', 'excel'], default='csv',
                       help='Input file format (default: csv)')
    parser.add_argument('--title_analysis', action='store_true',
                       help='Perform word frequency analysis on titles')
    parser.add_argument('--abstract_analysis', action='store_true',
                       help='Perform keyword extraction on abstracts')
    parser.add_argument('--topics', type=int, default=5,
                       help='Number of topics for topic modeling (default: 5)')
    parser.add_argument('--top_words', type=int, default=20,
                       help='Number of top words to display (default: 20)')
    parser.add_argument('--wordcloud', action='store_true',
                       help='Generate word cloud visualization')
    parser.add_argument('--trends', action='store_true',
                       help='Analyze publication trends over time')
    parser.add_argument('--all', action='store_true',
                       help='Perform all available analyses')
    return parser.parse_args()

def main():
    """Main execution function."""
    args = parse_args()
    
    # Download NLTK data if needed
    download_nltk_data()
    
    # Load data
    df = load_data(args.input_file, args.format)
    if df is None:
        return
    
    # If --all is specified, enable all analyses
    if args.all:
        args.title_analysis = True
        args.abstract_analysis = True
        args.wordcloud = True
        args.trends = True
    
    # Perform requested analyses
    word_freq = None
    
    if args.title_analysis or (not args.abstract_analysis and not args.trends):
        # Default to title analysis if nothing else specified
        if 'title' in df.columns:
            word_freq = analyze_word_frequency(df, 'title', args.top_words)
        else:
            print("Warning: 'title' column not found in data.")
    
    if args.abstract_analysis:
        if 'abstract' in df.columns:
            extract_keywords_tfidf(df, 'abstract', args.top_words)
            perform_topic_modeling(df, 'abstract', args.topics, 10)
        else:
            print("\nWarning: 'abstract' column not found in data.")
            print("Try running the search with --include_extra to include abstracts.")
    
    if args.trends:
        analyze_publication_trends(df)
    
    if args.wordcloud and word_freq:
        generate_wordcloud(word_freq)
    
    print(f"\n{'='*60}")
    print("Analysis complete! Check nlp_analysis.log for details.")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
