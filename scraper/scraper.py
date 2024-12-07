import time
import queue
import logging
import itertools
import threading
import requests
from config.config_loader import load_config
from concurrent.futures import ThreadPoolExecutor, as_completed
from scraper.save_db import save_to_db
from scraper.fetch import get_page_source, get_relevant_links, get_downstream_links

# Setup basic logging
logging.basicConfig(level=logging.INFO)

config = load_config()
dbName = config["database"]
# Keywords or labels to help the model prioritize relevant links
labels = config["labels"]
workers = config["workers"]
maxDepth = config["maxDepth"]

def scrape_complete_page(urls, max_workers):
    depth = 0
    downstream_links = scrape_page(urls, max_workers)
    while len(downstream_links) > 0 and depth < maxDepth:
        depth += 1
        logging.info(f"Scraping: {len(downstream_links)} downstream links at depth {depth}")
        downstream_links = scrape_page(downstream_links, max_workers)

def scrape_single_page(url):
    """Scrape a single URL and return the relevant links."""
    try:
        logging.info(f"Scraping: {url}")
        page_source = get_page_source(url)
        if not page_source:
            return []
        logging.info(f"Got Page Source for {url}")
        tic = time.perf_counter()
        relevant_links = get_relevant_links(url, page_source)
        toc = time.perf_counter()
        print(f"Downloaded the tutorial in {toc - tic:0.4f} seconds")
        logging.info(f"Got {len(relevant_links)} relevant links")
        save_to_db(relevant_links)
        logging.info("Saved relevant link to the database.")

        return get_downstream_links(url, page_source)

    except requests.exceptions.RequestException as e:
        logging.error(f"Error scraping {url}: {e}")
        return []

def scrape_page(urls, workers):
    """Scrape multiple URLs concurrently using ThreadPoolExecutor."""
    if not urls:
        return []
        
    downstream_links = []
    logging.info(f"Running with {workers} workers")
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_url = {executor.submit(scrape_single_page, url): url for url in urls}

    # Wait for each result as they are done
    for future in as_completed(future_to_url):
        url = future_to_url[future]
        try:
            result = future.result()
            print (url, future, result)
            if result:
                downstream_links.extend(result)
        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
    
    logging.info(f"Got {len(downstream_links)} downstream links from parallel processing.")
    return downstream_links


def queue_listener(event_queue):
    """Simulate an event listener that listens for new URL lists and processes them."""
    while True:
        # Wait for a new list of URLs to scrape
        url_list = event_queue.get()  # Blocks until a new task is available
        if url_list == "STOP":
            logging.info("Received stop signal. Exiting listener.")
            break
        # Call the event listener callback to process the URL list
        process_url_list(url_list, workers)

# Define the event listener (callback) function for processing URLs
def process_url_list(url_list, workers):
    """Event listener function to handle the URL list and start scraping"""
    logging.info(f"Received a list of {len(url_list)} URLs to scrape.")
    scraped_links = scrape_complete_page(url_list, max_workers=workers)  # Process URLs with concurrency
    logging.info(f"Scraping complete")
    return scraped_links

# Main function to simulate adding tasks to the event queue
def main2():
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
def main():
    url = ['https://www.bozeman.net/'] # Replace with your target URL
    
    urls1 = [
        "https://www.asu.edu/",
        "https://www.boerneisd.net/",
    ]
    scrape_complete_page(urls1, workers)
    #scrape_complete_page(url, workers)



if __name__ == "__main__":
    main()
