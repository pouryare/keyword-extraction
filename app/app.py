import streamlit as st
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import nltk
from nltk.tokenize import word_tokenize
from nltk.probability import FreqDist
import re
import random

# Fallback tokenization function
def simple_tokenize(text):
    return re.findall(r'\b\w+\b', text.lower())

# Download necessary NLTK data
@st.cache_resource
def download_nltk_data():
    try:
        nltk.download('punkt', quiet=True)
    except Exception as e:
        st.warning(f"Failed to download NLTK data: {str(e)}. Using fallback tokenization.")

download_nltk_data()

# Function to determine if dark mode is enabled
def is_dark_mode():
    return st.config.get_option("theme.base") == "dark"

# Function to get a color suitable for both dark and light modes
def get_neutral_color():
    return "#555555"  # A medium gray that should be visible in both modes

# Load the saved models
@st.cache_resource
def load_models():
    base_path = os.getcwd()
    vectorizer = joblib.load(os.path.join(base_path, 'keywords-tfidf-vectorizer.joblib'))
    feature_names = joblib.load(os.path.join(base_path, 'keywords-feature-names.joblib'))
    return vectorizer, feature_names

vectorizer, feature_names = load_models()

def pre_process(text):
    # Convert to lowercase and remove special characters
    text = re.sub(r'[^a-zA-Z\s]', '', text.lower())
    return text

def sort_coo(coo_matrix):
    tuples = zip(coo_matrix.col, coo_matrix.data)
    return sorted(tuples, key=lambda x: (x[1], x[0]), reverse=True)

def extract_topn_from_vector(feature_names, sorted_items, topn=10):
    sorted_items = sorted_items[:topn]
    score_vals = []
    feature_vals = []

    for idx, score in sorted_items:
        score_vals.append(round(score, 3))
        feature_vals.append(feature_names[idx])

    results = {}
    for idx in range(len(feature_vals)):
        results[feature_vals[idx]] = score_vals[idx]

    return results

@st.cache_data
def get_keywords_text(docs):
    # Preprocess the input text
    docs = pre_process(docs)
    
    # Generate tf-idf for the given document
    tf_idf_vector = vectorizer.transform([docs])

    sorted_items = sort_coo(tf_idf_vector.tocoo())
    keywords = extract_topn_from_vector(feature_names, sorted_items, 10)

    return keywords

def generate_wordcloud(text):
    def color_func(*args, **kwargs):
        return "hsl(%d, 80%%, 50%%)" % random.randint(0, 360)
    
    wordcloud = WordCloud(width=800, height=400, background_color=None, 
                          mode="RGBA", color_func=color_func, prefer_horizontal=0.7).generate(text)
    return wordcloud

@st.cache_data
def get_word_freq(text):
    try:
        words = word_tokenize(text)
    except LookupError:
        words = simple_tokenize(text)
    fdist = FreqDist(words)
    return fdist

st.title("Keyword Extraction App")

with st.form("keyword_extraction_form"):
    text_input = st.text_area("Enter your text here:")
    submitted = st.form_submit_button("Extract Keywords")

if submitted:
    if text_input:
        # Keyword Extraction
        keywords = get_keywords_text(text_input)
        
        st.subheader("Extracted Keywords:")
        for word, score in keywords.items():
            st.write(f"{word}: {score}")
        
        # Word Cloud
        st.subheader("Word Cloud:")
        wordcloud = generate_wordcloud(text_input)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        fig.patch.set_alpha(0)
        st.pyplot(fig)
        
        # Word Frequency Distribution
        st.subheader("Word Frequency Distribution:")
        fdist = get_word_freq(text_input)
        top_words = dict(fdist.most_common(20))
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Set the style to remove background grid
        plt.style.use('seaborn-v0_8-whitegrid')
        sns.set_style("whitegrid", {'axes.grid' : False})
        
        # Create the bar plot
        bars = sns.barplot(x=list(top_words.keys()), y=list(top_words.values()), ax=ax, color='magenta')
        
        # Remove the top and right spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color(get_neutral_color())
        
        # Customize the plot
        plt.title('Top 20 Most Frequent Words', color=get_neutral_color())
        plt.xlabel('Words', color=get_neutral_color())
        plt.ylabel('Frequency', color=get_neutral_color())
        plt.xticks(rotation=45, ha='right', color=get_neutral_color())
        plt.yticks(color=get_neutral_color())
        
        # Remove the background color of the plot
        ax.set_facecolor('none')
        fig.patch.set_alpha(0)
        
        # Adjust layout and display the plot
        plt.tight_layout()
        st.pyplot(fig)
        
        # Text Statistics
        st.subheader("Text Statistics:")
        try:
            words = word_tokenize(text_input)
        except LookupError:
            words = simple_tokenize(text_input)
        
        word_count = len(words)
        sentence_count = len(re.findall(r'\w+[.!?]', text_input))
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
        
        st.write(f"Word Count: {word_count}")
        st.write(f"Sentence Count: {sentence_count}")
        st.write(f"Average Word Length: {avg_word_length:.2f}")
        
    else:
        st.warning("Please enter some text to analyze.")

st.sidebar.title("About")
st.sidebar.info(
    "This app performs keyword extraction and text analysis using TF-IDF. "
    "Enter your text in the input box and click 'Extract Keywords' to see the results."
)