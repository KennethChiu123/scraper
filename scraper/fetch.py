
import re
import time
import urllib
import random
import logging
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from transformers import pipeline
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

# Setup basic logging
logging.basicConfig(level=logging.INFO)

# Initialize HuggingFace model for text classification (we'll use a simple model here)
nlp = pipeline("zero-shot-classification")

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


# Function to scrape and identify relevant links
def scrape_and_filter_links(url):
    # Send HTTP request to the URL
    text = None
    response = fetch(url)
    logging.info(f"Got {url} with status code {response.status_code}.")
    if response.status_code == 200:
        text = response.text
    else:
        text = get_source(url)
    
    if text == None:
        return []
    # Parse HTML content
    soup = BeautifulSoup(text, 'html.parser')
    
    # Find all <a> tags (links)
    links = soup.find_all('a', href=True)

    # Filter links using ML model (zero-shot classification)
    relevant_links = []
    for link in links:
        text = link.get_text().strip()
        href = link['href']
        
        # Ensure that the 'text' is non-empty and the 'labels' are valid
        if text:
            # Run classification on the link text
            result = nlp(text, candidate_labels=labels)
            
            # Check if the link is relevant (e.g., high score for "contact", "budget", etc.)

            # example: {'sequence': 'Jobs', 'labels': ['important', 'report', 'contact', 'PDF', 'ACFr', 'financial', 'budget'], '
            # scores': [0.6557594537734985, 0.09940328449010849, 0.08661620318889618, 0.05602235347032547, 
            # 0.047790899872779846, 0.03889332339167595, 0.015514509752392769]}
            if any(label in result['labels'][0] for label in labels):  # Heuristic to choose high-value links

                #skip bad scores
                if result['scores'][0] < 0.5:
                    continue

                logging.debug(f"Got {url} with href {href} and score: {result['scores'][0]}.")
                relevant_links.append({
                    "url": url,
                    "text": text,
                    "href": href,
                    "classification": result['labels'][0],
                    "relevance_score": result['scores'][0]
                })
    
    return relevant_links