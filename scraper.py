import re
from urllib.parse import urlparse, urljoin
# To find the other embedded URLs
from bs4 import BeautifulSoup

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

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

    return lists_to_check

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        # Gets the domain of the URL
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        # This checks what domains not to use
        # Add domains to use
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