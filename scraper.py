import re
from urllib.parse import urlparse, urljoin, urldefrag
from datasketch import MinHash, MinHashLSH
# To find the other embedded URLs
from bs4 import BeautifulSoup
import os
import hashlib
import unicodedata


import json

def scraper(url, resp, frontier):
    if resp.status != 200:
        print(f"The error: {resp.error} occurred. The status of this error is {resp.status}")
        return list()
    
      # Check encoding and set default to 'utf-8'
    content_type = resp.raw_response.headers.get('content-type', '').lower()
    encoding = 'utf-8'  # Default to UTF-8 if charset is not specified
    if 'charset=' in content_type:
        encoding = content_type.split('charset=')[-1]

    try:
        # Decode and re-encode to ensure UTF-8
        content = resp.raw_response.content.decode(encoding, errors='ignore').encode('utf-8')
    except LookupError:
        print(f"Warning: Unknown encoding '{encoding}' for URL {url}. Defaulting to UTF-8.")
        content = resp.raw_response.content.decode('utf-8', errors='ignore')
        
    soup = BeautifulSoup(content, 'html.parser')
    if is_duplicate(url, soup, frontier):
        return list()
    links = extract_next_links(soup, url, resp, frontier)
    new_links = [link for link in links if is_valid(link)]
    # new_links = [link for link in links if is_valid(link) and not is_duplicate(soup, frontier)]
    return new_links


def extract_text_from_page(soup, url, frontier, folder_name="tokens_by_subdomain"): #content is a string
    # Remove script and style elements from the HTML
    for element in soup(['script', 'style']):
        element.decompose()

    curr_tokens = [] 
    word_count = 0
    # Function to clean and normalize text
    def clean_text(text):
        # Normalize Unicode characters (NFKD decomposes characters into their basic components)
        normalized_text = unicodedata.normalize("NFKD", text)

        # Remove control characters (non-printable characters)
        cleaned_text = re.sub(r'[\x00-\x1F\x7F]', '', normalized_text)

        # Decode any unicode escape sequences and handle UTF-8 double encoding
        try:
            # First attempt: decode from UTF-8 and escape sequences (unicode_escape)
            cleaned_text = bytes(cleaned_text, "utf-8").decode("unicode_escape")
        except UnicodeDecodeError:
            # If above fails (e.g., due to double encoding), try re-decoding from byte sequence
            cleaned_text = cleaned_text.encode('utf-8').decode('utf-8')

        return cleaned_text

    # Function to check if a word contains valid, readable characters
    def is_valid_word(word):
        # Ignore words that contain unwanted characters (e.g., unicode escape sequences, non-ASCII)
        if re.search(r'[^\x00-\x7F]+', word):  # This matches any non-ASCII character
            return False
        return True

    # Extract all visible text content
    for text in soup.stripped_strings:
        # Clean and normalize the text
        cleaned_text = clean_text(text)

        # Split into words
        words = cleaned_text.split()  # Splits if there is a space

        # Filter valid words
        valid_words = [word for word in words if is_valid_word(word)]
        word_count += len(valid_words)

        # Add valid words to curr_tokens list
        curr_tokens.extend(valid_words)  # Only add filtered words to curr_tokens list

    # Check if it is our longest page (highest word_count)
    if word_count:
        frontier.add_potential_longest_page(url, word_count, curr_tokens)

    # Avoid low information pages 
    if word_count < 125:
        print()
        print(f"LOW DOCUMENT page! {url}")
        print()
        return 
    
    parsed_url = urlparse(url) #parse the url to get the hostname for organizing json files
    curr_subdomain = parsed_url.hostname #Get subdomain from the URL
    

    

    #defines the path to the json file
    json_tokens_file_path = os.path.join(folder_name, f"{curr_subdomain}.json")


    with frontier._lock:
        #Checks if the json file for the subdomain exists already
        if os.path.exists(json_tokens_file_path):
            with open(json_tokens_file_path, "r") as file:
                existing_tokens = json.load(file)
            # Initialize the emptylist if the subdomain does not exist
            if curr_subdomain not in existing_tokens:
                existing_tokens[curr_subdomain] = []

            # Add url : raw words
            existing_tokens[curr_subdomain].append({url: curr_tokens})

            page_count = existing_tokens.get("page_count", 0) + 1
            tokens_to_save = {
                "page_count": page_count,
                **{k: v for k, v in existing_tokens.items() if k != "page_count"}
            }
        else:
            # Create new tokens dictionary if file doesn't exist
            tokens_to_save = {
            "page_count": 1,
            curr_subdomain: [{url: curr_tokens}]
        }
        
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
    
    extract_text_from_page(soup, resp.url, frontier)

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
    invalid_domains = {"mse.ics.uci.edu", "tippers.ics.uci.edu", "mhcis.ics.uci.edu", "sites.google.com"}
    try:
        parsed = urlparse(url)

        if parsed.scheme not in set(["http", "https"]):
            return False

        if parsed.netloc.lower() in invalid_domains:
            return False

        if not re.match(
            r'^(\w*.)(ics.uci.edu|cs.uci.edu|stat.uci.edu|informatics.uci.edu|today.uci.edu\/department\/information_computer_sciences)$',parsed.netloc):
            return False
        
        disallowed_keywords = ["Image", "image", "pps", "github", "date", "ical", "outlook", "event", "music", "media", "video", "account", "unsubscribe", "login", "lang", "mailto", "redirect", "attachment", "print", "version", "view", "format", "gitlab", "from", "-/tree", "action", "-/compare", "-/commit", ".tar.gz", ".xlsx", ".rar", ".zip", ".docx", ".wav", ".mp3", ".mp4", ".gif", ".png", ".jpeg", ".jpg", ".diff", ".org","idx",".txt", ".odc", "ical","?tribe__ecp_custom_",".ppsx","?rev=","?do=",".com","date","calendar","?view=agenda","?calendar=","?tribe-bar-date","filter","share", "pdf", "redirect", "#comment", "#respond", "#comments", "img"]
        if any(keyword in url for keyword in disallowed_keywords):
            return False
        
        if "uci.edu" not in url:
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
            + r"|ogg|ogv|ram|m4v|scm"
            + r"|rtf|epub|thmx|mso|arff"
            + r"|bin|msi|jar|exe|dll|ps"
            + r"|bz2|7z|dmg|iso|tgz|gz|wmv"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())


    except TypeError:
        print ("TypeError for ", parsed)
        raise
    # https://github.com/Araz-cs/spacetime-crawler4py121/blob/master/scraper.py


def is_duplicate(url, soup, frontier, threshold=0.85, perms=128):
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
    similar_docs = frontier.similar_docs(minhash)
    
    # If similar documents are found, consider them duplicates
    if similar_docs:
        print()
        print(f"DUPLICATE page: {url}")
        print(f"ORIGINAL page: {similar_docs[0]}")
        print(f"-------------------------")
        return True
    

        print("-------------------------")    # If no duplicates found, add this document to the indexes
    frontier.add_seen_hashes(content_hash)
    frontier.lsh_insert(minhash)
    return False

