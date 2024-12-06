import pytest
from scraper.scraper import scrape_and_filter_links





def test_scrape_and_filter_links():
    url = "https://www.a2gov.org/"
    links = scrape_and_filter_links(url)
    assert len(links) > 0  # You should check some other conditions as well
