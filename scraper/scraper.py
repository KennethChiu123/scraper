import time
import queue
import logging
import itertools
import threading
import requests
from config.config_loader import load_config
from concurrent.futures import ThreadPoolExecutor, wait
from scraper.save_db import save_to_db
from scraper.fetch import scrape_and_filter_links

# Setup basic logging
logging.basicConfig(level=logging.INFO)

config = load_config()
dbName = config["database"]
# Keywords or labels to help the model prioritize relevant links
labels = config["labels"]
workers = config["workers"]

def scrape_page(url):
    """Scrape a single URL and return the relevant links."""
    try:
        logging.info(f"Scraping: {url}")
        links = scrape_and_filter_links(url)
        logging.info(f"Found {len(links)} relevant links on {url}")
        save_to_db(links)
        logging.info("Saved relevant links to the database.")
        return links

    except requests.exceptions.RequestException as e:
        logging.error(f"Error scraping {url}: {e}")
        return []

def scrape_all(urls, max_workers=workers):
    """Scrape multiple URLs concurrently using ThreadPoolExecutor."""
    thread_list = []
    logging.info(f"Running with {workers} workers")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for url in urls:
            thread_list.append(executor.submit(scrape_page, url))

    wait(thread_list)
    
    # Collect the results from the futures
    aggregated_data = [future.result() for future in thread_list]
    links = list(itertools.chain(*aggregated_data))
    
    return links


def queue_listener(event_queue):
    """Simulate an event listener that listens for new URL lists and processes them."""
    while True:
        # Wait for a new list of URLs to scrape
        url_list = event_queue.get()  # Blocks until a new task is available
        if url_list == "STOP":
            logging.info("Received stop signal. Exiting listener.")
            break
        # Call the event listener callback to process the URL list
        process_url_list(url_list)

# Define the event listener (callback) function for processing URLs
def process_url_list(url_list):
    """Event listener function to handle the URL list and start scraping"""
    logging.info(f"Received a list of {len(url_list)} URLs to scrape.")
    scraped_links = scrape_all(url_list, max_workers=workers)  # Process URLs with concurrency
    logging.info(f"Scraping complete, found {len(scraped_links)} links.")
    return scraped_links

# Main function to simulate adding tasks to the event queue
def main():
    # Create a queue to simulate event-driven task management
    event_queue = queue.Queue()

    # Start the listener in a separate thread
    listener_thread = threading.Thread(target=queue_listener, args=(event_queue,))
    listener_thread.daemon = True
    listener_thread.start()

    list1 = [
        "https://www.a2gov.org/ ",
        "https://www.bozeman.net/",
    ]
    list2 = [
        "https://www.asu.edu/",
        "https://www.boerneisd.net/",
    ]

    logging.info("Sending URL list 1 to the scraper...")
    # Send URL list to the event listener
    event_queue.put(list1)  
    
    # Simulate wait between tasks
    time.sleep(2)  

    logging.info("Sending URL list 2 to the scraper...")
    # Send another URL list to the event listener
    event_queue.put(list2)  

    # Stop the listener after all tasks are processed
    # Use "STOP" signal to gracefully terminate the listener thread
    event_queue.put("STOP")
    # Wait for the listener thread to finish
    listener_thread.join()  


#test
def main_test():
    url = 'https://www.bozeman.net/'  # Replace with your target URL
    
    urls1 = [
        "https://www.asu.edu/",
        "https://www.boerneisd.net/",
    ]
    #scrape_all(urls1, workers)
    #scrape_page(url)



if __name__ == "__main__":
    main()
