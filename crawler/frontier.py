import os
import shelve
import threading
from threading import Thread, RLock
from queue import Queue, Empty
import queue
from utils import get_logger, get_urlhash, normalize
from scraper import is_valid
from datasketch import MinHash, MinHashLSH
import json


class Frontier(object):
    def __init__(self, config, restart, folder_name="tokens_by_subdomain"):
        self.logger = get_logger("FRONTIER")
        self.config = config
        self.to_be_downloaded = queue.Queue()
        self.url_cooldowns = {}
        self._lock = threading.Lock()
        #create lock functions
        self.visited_urls = set()
        self.seen_hashes = set() 
        # Set to 4 to get the four main links first
        self.doc_count = 4
        self.lsh = MinHashLSH(threshold=0.85, num_perm=128)
        self.longest_page = {}  # Holds URL:Length of longest page for report requirement #2

        self.stats_file_path = "frontier_data.json"

        
        if not os.path.exists(self.config.save_file) and not restart:
            # Save file does not exist, but request to load save.
            self.logger.info(
                f"Did not find save file {self.config.save_file}, "
                f"starting from seed.")
        elif os.path.exists(self.config.save_file) and restart:
            # Save file does exists, but request to start from seed.
            self.logger.info(
                f"Found save file {self.config.save_file}, deleting it.")
            os.remove(self.config.save_file)
        # Load existing save file, or create one if it does not exist.
        self.save = shelve.open(self.config.save_file)
        if restart:
            for url in self.config.seed_urls:
                self.add_url(url)
        else:
            # Set the frontier state with contents of save file.
            self._parse_save_file()
            if not self.save:
                for url in self.config.seed_urls:
                    self.add_url(url)

    def _parse_save_file(self):
        ''' This function can be overridden for alternate saving techniques. '''
        total_count = len(self.save)
        tbd_count = 0
        for url, completed in self.save.values():
            if not completed and is_valid(url):
                self.to_be_downloaded.put(url)
                tbd_count += 1
        self.logger.info(
            f"Found {tbd_count} urls to be downloaded from {total_count} "
            f"total urls discovered.")

    def get_tbd_url(self):
        try:
            return self.to_be_downloaded.get()
        except IndexError:
            return None
        except KeyError:
            return None

    def add_url(self, url):
        url = normalize(url)
        urlhash = get_urlhash(url)
        with self._lock:
            if urlhash not in self.save:
                self.save[urlhash] = (url, False)
                self.save.sync()
                self.to_be_downloaded.put(url)

    
    def mark_url_complete(self, url):
        urlhash = get_urlhash(url)
        with self._lock:
            if urlhash not in self.save:
                # This should not happen.
                self.logger.error(
                    f"Completed url {url}, but have not seen it before.")

            self.save[urlhash] = (url, True)
            self.save.sync()

    def get_cooldown(self, url):
        with self._lock:
            return self.url_cooldowns.get(url, 0)
    
    def update_url_cooldown(self, url, cooldown):
        with self._lock:
            self.url_cooldowns[url] = cooldown

    def add_potential_longest_page(self, url, length):
        with self._lock:
            if len(self.longest_page) == 0: # First page to be appended to longest_page
                self.longest_page[url] = length
            elif len(self.longest_page) > 1:    # Error of having more than 1 item in our dictionary holding longest
                raise ValueError("longest_page dictionary should only contain one key-value pair.")
            else:
                curr_length = next(iter(self.longest_page.values())) # Check if this new page length is longer than the max rn
                if length > curr_length:
                    self.longest_page.clear()
                    self.longest_page[url] = length
        self._save_data_to_file()
    
    def _save_data_to_file(self):
        with self._lock:
            data = {
                "doc_count": len(self.visited_urls),
                "longest_page": self.longest_page
            }
            with open(self.stats_file_path, "w") as file:
                json.dump(data, file, indent=4)

    def process_url(self, url):
        '''
        Process a URL if it hasn't been seen before.
        '''
        urlhash = get_urlhash(url)  # Assume this generates a unique hash for the URL
        if not self.check_duplicate_hash(urlhash):
            self.add_seen_hashes(urlhash)
        else:
            self.logger.info(f"Duplicate URL detected, skipping: {url}")

    def lsh_insert(self, minhash):
        with self._lock:
            self.lsh.insert(f"doc_{self.doc_count}", minhash)

    def add_seen_hashes(self, hash_value):
        with self._lock:
            if (hash_value) not in self.seen_hashes:
                self.seen_hashes.add(hash_value)
                
    def check_duplicate_hash(self, hash_value):
        with self._lock:
            return hash_value in self.seen_hashes

    def add_visited_url(self, url):
        with self._lock:
            self.visited_urls.add(url)

    def in_visited_urls(self, url):
        with self._lock:
            return url in self.visited_urls
        
    def get_to_be_downloaded_urls(self):
        with self._lock:
            return self.to_be_downloaded