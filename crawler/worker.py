from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time
import tldextract

class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        self.run_again = True
        
    def run(self):
        while True:
            # Gets the url from the frontier
            tbd_url = self.frontier.get_tbd_url()

            # Only exit if it tries it twice and there are no more urls to expand on
            if not tbd_url and self.run_again:
                time.sleep(5000)
                self.run_again = False
                continue
            # Checks if no more crawlers to use
            elif not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            # Get the domain without the subdomains
            domain = tldextract.extract(tbd_url).domain
            
            # Check if the domain is currently being used

            if domain in self.frontier.url_cooldowns:
                elapsed_time = time.time() - self.frontier.url_cooldowns[domain]

                if elapsed_time < self.config.time_delay:
                    waiting_time = self.config.time_delay - elapsed_time
                    time.sleep(waiting_time)
                    self.frontier.append(tbd_url)
                    continue
                    

            self.run_again = True

            # Put the latest time the domain has been requested
            self.frontier.url_cooldowns[domain] = time.time()
            
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            # Mark that the url is complete
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
