import re
from urllib.parse import urlparse, urljoin, urldefrag
from datasketch import MinHash, MinHashLSH
# To find the other embedded URLs
from bs4 import BeautifulSoup
import os
import hashlib


import json

def scraper(url, resp, frontier):
    if resp.status != 200:
        print(f"The error: {resp.error} occurred. The status of this error is {resp.status}")
        return list()
    
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    links = extract_next_links(soup, url, resp, frontier)
    new_links = [link for link in links if is_valid(link)]
    # new_links = [link for link in links if is_valid(link) and not is_duplicate(soup, frontier)]
    return new_links


def extract_text_from_page(soup, url, frontier, folder_name="tokens_by_subdomain"): #content is a string
    curr_tokens = [] # TODO: SHOULD BE A JSON INSTEAD

    # Extract all text content
    for text in soup.stripped_strings: 
        # Split into words
        words = text.split() #splits if there is a space
        word_count = len(words)
        curr_tokens.extend(words) #ONLY add filtered words to curr_tokens list
    
    parsed_url = urlparse(url) #parse the url to get the hostname for organizing json files
    curr_subdomain = parsed_url.hostname #Get subdomain from the URL


    #defines the path to the json file
    json_tokens_file_path = os.path.join(folder_name, f"{curr_subdomain}.json")


    with frontier._lock:
        #Checks if the json file for the subdomain exists already
        if os.path.exists(json_tokens_file_path):
            with open(json_tokens_file_path, "r") as file:
                existing_tokens = json.load(file)
                # Add current tokens to existing ones
                existing_tokens[curr_subdomain] = existing_tokens.get(curr_subdomain, []) + curr_tokens
                tokens_to_save = existing_tokens
        else:
            # Create new tokens dictionary if file doesn't exist
            tokens_to_save = {curr_subdomain: curr_tokens}
        
        # Save tokens to file
        with open(json_tokens_file_path, "w") as file:
            json.dump(tokens_to_save, file, indent=4)

    

def extract_next_links(soup, url, resp, frontier):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    
    # Checks if the response status is valid
    if resp.status != 200:
        print(f"The error: {resp.error} occurred. The status of this error is {resp.status}")
        return list()
    
    extract_text_from_page(soup, resp.raw_response.url, frontier)

    lists_to_check = []

    # Goes through every found link
    # href is the type of link to make sure it is a link
    for link in soup.find_all('a', href=True):
        # extract the url section of it
        possible_url = link['href']
        # if the possible_url is not complete, join it with the original url, otherwise it ignores the original
        entire_url = urljoin(url, possible_url)
        # Gets rid of fragmentation
        defragged_url, fragment = urldefrag(entire_url)
    
        # append it to the list
        lists_to_check.append(defragged_url)

    
    return lists_to_check

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    # Add Functionality to check if the URL contains one of the 5 valid domains
        # use VALID_URLS
    #Got 600-608 errors here
    invalid_domains = {"mse.ics.uci.edu", "tippers.ics.uci.edu", "mhcis.ics.uci.edu"}
    try:
        parsed = urlparse(url)

        if parsed.scheme not in set(["http", "https"]):
            return False


        if parsed.netloc.lower() in invalid_domains:
            return False

        if not re.match(
            r'^(\w*.)(ics.uci.edu|cs.uci.edu|stat.uci.edu|informatics.uci.edu|today.uci.edu\/department\/information_computer_sciences)$',parsed.netloc):
            return False
        
        disallowed_keywords = ["filter","?share=", "pdf", "redirect", "#comment", "#respond", "#comments"]
        if any(keyword in url for keyword in disallowed_keywords):
            return False
        
        # Check for repetitive path patterns
        if re.search(r'(\/\w+\/)\1{2,}', parsed.path):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())


    except TypeError:
        print ("TypeError for ", parsed)
        raise
    # https://github.com/Araz-cs/spacetime-crawler4py121/blob/master/scraper.py


def is_duplicate(soup, frontier, threshold=0.85, perms=128):
    content = str(soup)
    # Generate a SHA-256 hash of the content
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    # Check for duplicate by verifying if hash is in `seen_hashes`
    if frontier.check_duplicate_hash(content_hash):
        return True # Duplicate content
    
    # Get clean text
    text = soup.get_text(separator=' ', strip=True).lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Create MinHash for current content
    minhash = MinHash(num_perm=perms)
    for i in range(len(text) - 3 + 1):
        shingle = text[i:i + 3]
        minhash.update(shingle.encode('utf-8'))
    
    # Check for near duplicates using `query`
    similar_docs = frontier.lsh.query(minhash)
    
    # If similar documents are found, consider them duplicates
    if similar_docs:
        return True
    
    # If no duplicates found, add this document to the indexes
    frontier.add_seen_hashes(content_hash)
    frontier.lsh_insert(minhash)
    #frontier.increment_doc_count()
    return False

