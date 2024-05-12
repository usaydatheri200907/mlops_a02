from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import requests
from bs4 import BeautifulSoup
import csv
import re  # Added import for regular expressions
from nltk.tokenize import word_tokenize  # Added import for word tokenization
from nltk.corpus import stopwords  # Added import for stopwords
from nltk.stem import WordNetLemmatizer  # Added import for lemmatization

def extract_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    links = []
    titles = []
    descriptions = []
    
    for link in soup.find_all('a'):
        links.append(link.get('href'))
    
    articles = soup.find_all('article')
    for article in articles:
        title_tag = article.find('h2')
        description_tag = article.find('p')
        
        if title_tag and description_tag:
            title = title_tag.get_text()
            description = description_tag.get_text()
            titles.append(title)
            descriptions.append(description)
    
    return links, titles, descriptions

def clean_text(text):
    clean_text = re.sub(r'<.*?>', '', text)
    clean_text = re.sub(r'[^a-zA-Z]', ' ', clean_text)
    clean_text = clean_text.lower()
    tokens = word_tokenize(clean_text)
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [word for word in tokens if word not in stop_words]
    lemmatizer = WordNetLemmatizer()
    lemmatized_tokens = [lemmatizer.lemmatize(word) for word in filtered_tokens]
    clean_text = ' '.join(lemmatized_tokens)
    return clean_text

def write_to_csv(data, file_path):
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Title', 'Description'])
        for title, description in data:
            writer.writerow([title, description])

def process_data():
    dawn_url = 'https://www.dawn.com/'
    bbc_url = 'https://www.bbc.com/'
    
    dawn_links, dawn_titles, dawn_descriptions = extract_data(dawn_url)
    clean_dawn_titles = [clean_text(title) for title in dawn_titles]
    clean_dawn_descriptions = [clean_text(description) for description in dawn_descriptions]
    dawn_data = list(zip(clean_dawn_titles, clean_dawn_descriptions))
    write_to_csv(dawn_data, '/path/to/your/dawn_data.csv')
    
    bbc_links, bbc_titles, bbc_descriptions = extract_data(bbc_url)
    clean_bbc_titles = [clean_text(title) for title in bbc_titles]
    clean_bbc_descriptions = [clean_text(description) for description in bbc_descriptions]
    bbc_data = list(zip(clean_bbc_titles, clean_bbc_descriptions))
    write_to_csv(bbc_data, '/path/to/your/bbc_data.csv')

# Here begins the step 4 

# Define default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 5, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Instantiate DAG
dag = DAG(
    'mlops_dag',
    default_args=default_args,
    description='MLOps DAG for data extraction, transformation, and storage',
    schedule_interval='@daily',
)

# Define tasks
extract_transform_task = PythonOperator(
    task_id='extract_transform_data',
    python_callable=process_data,
    dag=dag,
)

# Set task dependencies
extract_transform_task
