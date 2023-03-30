from bs4 import BeautifulSoup
from urllib.parse import urlparse
from settings import *

with open('blacklist.txt') as f:
    BAD_DOMAINS = set(f.read().splitlines())


def get_page_content(row):
    soup = BeautifulSoup(row['html'])
    text = soup.get_text()
    return text


def tracker_urls(row):
    soup = BeautifulSoup(row['html'])
    scripts = soup.find_all('script', {'src': True})
    srcs = [script.get('src') for script in scripts]

    links = soup.find_all('a', {'href': True})
    hrefs = [link.get('href') for link in links]

    all_domains = [urlparse(src).hostname for src in srcs + hrefs]
    bad_domains = [domain for domain in all_domains if domain in BAD_DOMAINS]
    return len(bad_domains)


class Filter:
    def __init__(self, results):
        self.filtered = results.copy()

    # filtering by result content
    def content_filter(self):
        page_content = self.filtered.apply(get_page_content, axis=1)
        word_count = page_content.apply(lambda x: len(x.split(" ")))
        word_count /= word_count.median()

        word_count[word_count <= .5] = RESULT_COUNT
        word_count[word_count != RESULT_COUNT] = 0
        self.filtered['rank'] = word_count

    # filtering by ads and trackers
    def tracker_filter(self):
        tracker_count = self.filtered.apply(tracker_urls, axis=1)
        tracker_count[tracker_count > tracker_count.median()] = RESULT_COUNT * 2
        self.filtered['rank'] += tracker_count

    def filter(self):
        self.content_filter()
        self.tracker_filter()
        self.filtered = self.filtered.sort_values(by='rank', ascending=True)
        self.filtered['rank'] = self.filtered['rank'].round(0).astype(int)

        return self.filtered
