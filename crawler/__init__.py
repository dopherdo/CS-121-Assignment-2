from utils import get_logger
from crawler.frontier import Frontier
from crawler.worker import Worker
from urllib.parse import urlparse, urlunparse

class Crawler(object):
    def __init__(self, config, restart, frontier_factory=Frontier, worker_factory=Worker, unique_pages=set()):
        self.config = config
        self.logger = get_logger("CRAWLER")
        self.frontier = frontier_factory(config, restart)
        self.workers = list()
        self.worker_factory = worker_factory
        self.unique_pages = unique_pages

    # used for reporting #1 we can maintain a count of unique pages in Crawler.unique_pages
    # A unique page in the reporting context is a page that has a unique URL regardless of fragment
    def is_unique_page(self, url):
        # Parse the URL and discard the fragment
        parsed = urlparse(url)
        url_without_fragment = urlunparse(parsed._replace(fragment=""))

        # Check if the URL without fragment is unique
        if url_without_fragment in self.unique_pages:
            return False  # URL already exists, so it's not unique

        # Add the new URL to the set and return True
        self.unique_pages.add(url_without_fragment)
        return True

    def start_async(self):
        self.workers = [
            self.worker_factory(worker_id, self.config, self.frontier)
            for worker_id in range(self.config.threads_count)]
        for worker in self.workers:
            worker.start()

    def start(self):
        self.start_async()
        self.join()

    def join(self):
        for worker in self.workers:
            worker.join()
