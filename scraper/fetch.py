
import re
import time
import urllib
import random
import logging
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from transformers import pipeline
from urllib.parse import urlparse, urljoin
from config.config_loader import load_config
from selenium.webdriver.firefox.options import Options as FirefoxOptions

# List of common User-Agent strings
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:55.0) Gecko/20100101 Firefox/55.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36 Edge/13.0.802.164",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
]

config = load_config()
dbName = config["database"]
# Keywords or labels to help the model prioritize relevant links
labels = config["labels"]
relevanceThreshold = config["relevanceThreshold"]
maxDepth = config["maxDepth"]

# Setup basic logging
logging.basicConfig(level=logging.INFO)

# Initialize HuggingFace model for text classification (we'll use a simple model here)
nlp = pipeline("zero-shot-classification", device=0) # set to use GPU
summarizer = pipeline('summarization', model='t5-large', tokenizer='t5-large')

def get_firefox_options():
    options = FirefoxOptions()
    options.set_preference('devtools.jsonview.enabled', False)
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")
    options.add_argument("--disable-dev-shm-usage")

    return options

def remove_tags(text):
    TAG_RE = re.compile(r'<[^>]+>')
    return TAG_RE.sub('', text)

def get_domain(url):
    """Extract domain from a URL."""
    parsed_url = urlparse(url)
    return parsed_url.netloc  # Extract the domain (e.g., 'www.bozeman.net')

def get_source(url):
    browser = None
    try:
        logging.info(f"Using selenium as alternative for {url}.")
        options = get_firefox_options()
        browser = webdriver.Firefox(options)
        browser.get(url)
        # sleep to wait pass
        time.sleep(1) 
        return browser.page_source
    except Exception as e:
        logging.error(f"Got Error for {e}.")
    finally:
        if browser:
            browser.close()
    return []

def fetch(url):
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        "Referer": url,
        'Connection': 'keep-alive',
    }
    response = requests.get(
        url,
        headers=headers,
        timeout=5,
        allow_redirects=True,
        proxies=urllib.request.getproxies()
    )
    return response

def get_page_source(url):
    # Send HTTP request to the URL
    text = None
    response = fetch(url)
    logging.info(f"Got {url} with status code {response.status_code}.")
    if response.status_code == 200:
        text = response.text
    else:
        text = get_source(url)

    return text

# Function to scrape and identify relevant links
def get_relevant_links(url, page_source):
    
    relevant_links = []
    # Perform zero-shot classification on the page source
    classification_result = nlp(page_source, candidate_labels=labels)
    best_label = classification_result['labels'][0]
    relevance_score = classification_result['scores'][0]

    logging.info(f"Zero shot classification => {best_label}, {relevance_score}.")

    # If relevance score is below threshold, consider the page irrelevant
    if relevance_score < relevanceThreshold:
        return relevant_links

    #i went with summary over keywords
    soup = BeautifulSoup(page_source, 'html.parser')
    paragraphs = soup.get_text(separator=' ', strip=True)
    #logging.info(f"paragraphs => {paragraphs}.")
    generated_text = summarizer(paragraphs, min_length=10, max_length=100)
    logging.info(f"generated_text => {generated_text}.")
    #INFO:root:generated_text => [{'summary_text': "Ann Arbor's mission is to deliver exceptional services that sustain and enhance a vibrant, safe and diverse community . 
    # Apply  Pay  Volunteer  Request  Report Licenses & Permits Voter Registration Election Inspectors Tax Deferment Apply for a scholarship Parking Citation Property 
    # Tax Water Bill Solid Waste Bill Invoices Boards and Commissions Events GIVE 365 Natural Area Preservation Be the first to know when new information is available!"}].

    
    relevant_links.append({
        "url": url,
        "summary": generated_text[0]['summary_text'],
        "classification": best_label,
        "relevance_score": relevance_score
    })

    return relevant_links


def get_downstream_links(url, page_source):
    # Parse HTML content
    soup = BeautifulSoup(page_source, 'html.parser')

    # Get the domain of the current page
    base_domain = get_domain(url)

    links = soup.find_all('a', href=True)
    urls = []
    for link in links:
        href = link.get('href')
        # Make the URL absolute if it's relative
        absolute_url = urljoin(url, href)
        
        # Get the domain of the link
        link_domain = get_domain(absolute_url)
        
        # Compare the domain of the link to the base domain
        if link_domain == base_domain:
            # Add the link to the list if it matches the base domain
            urls.append(absolute_url)
    
    return urls