import re
from urllib.parse import urlparse, urljoin
# To find the other embedded URLs
from bs4 import BeautifulSoup
import os

import json

def scraper(url, resp):
    links = extract_next_links(url, resp)
    new_links = [link for link in links if is_valid(link)] 
    print(new_links)
    return new_links


def extract_text_from_page(content, url, folder_name="tokens_by_subdomain"): #content is a string
    soup = BeautifulSoup(content, 'html.parser') #Creates object to extract text from HTML Content"
    curr_tokens = [] # TODO: SHOULD BE A JSON INSTEAD
  
    # TODO: check to see if file (check subdomain) is already there

    # Extract all text content as tokens and filter out stopwords
    for text in soup.stripped_strings: 
        # Split into words and filter out stopwords
        words = text.split() #splits if there is a space
        curr_tokens.extend(words) #ONLY add filtered words to curr_tokens list
    
    parsed_url = urlparse(url) #parse the url to get the hostname for organizing json files
    curr_subdomain = parsed_url.hostname #Get subdomain from the URL
    
    os.makedirs(folder_name, exist_ok=True) #ensure the token folder exists

    #defines the path to the json file
    json_tokens_file_path = os.path.join(folder_name, f"{curr_subdomain}.json")

    #Checks if the json file for the subdomain exists already
    if os.path.exists(json_tokens_file_path):
        with open(json_tokens_file_path, "r") as file:
            subdomain_tokens = json.load(file) #loads existing tokens
    else:
        subdomain_tokens = [] #empty file
    

    
    #append current tokens to existing tokens (could include duplicates)
    subdomain_tokens[curr_subdomain] = subdomain_tokens.get(curr_subdomain, []) + curr_tokens

    
    #saves tokens to the file with good formatting
    with open(json_tokens_file_path, "w") as file:
        json.dump(subdomain_tokens, file, indent=4)
    

    

def extract_next_links(url, resp):
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
    
    extract_text_from_page(resp.raw_response.content, resp.raw_response.url)

    # Parses the content and finds all of the other links in the text
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')

    lists_to_check = []

    # Goes through every found link
    # href is the type of link to make sure it is a link
    for link in soup.find_all('a', href=True):
        # extract the url section of it
        possible_url = link['href']
        # if the possible_url is not complete, join it with the original url, otherwise it ignores the original
        entire_url = urljoin(url, possible_url)
        # append it to the list
        lists_to_check.append(entire_url)

    # Print each URL as you find it
    for url in lists_to_check:
        print("Found URL:", url)  # Or use logging for file output

    print("Lists_to_check:")
    print(lists_to_check)
    print()

    return lists_to_check

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    # Add Functionality to check if the URL contains one of the 5 valid domains
        # use VALID_URLS
    try:
        parsed = urlparse(url)

        if parsed.scheme not in set(["http", "https"]):
            return False
        if not re.match(
            r'^(\w*.)(ics.uci.edu|cs.uci.edu|stat.uci.edu|today.uci.edu\/department\/information_computer_sciences)$',parsed.netloc):
            return False
        
        disallowed_keywords = ["?share=", "pdf", "redirect", "#comment", "#respond", "#comments"]
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


# check with sha-256 for exact or near page duplicates
def not_duplicate(url):
    pass
