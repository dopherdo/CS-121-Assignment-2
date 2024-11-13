#CHATGPT

import json
import os


stopwords = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "aren't", "as", "at", "be", "because", "been",
    "before", "being", "below", "between", "both", "but", "by", "can't",
    "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't",
    "doing", "don't", "down", "during", "each", "few", "for", "from", "further",
    "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd",
    "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself",
    "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into",
    "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most",
    "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once",
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over",
    "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should",
    "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their",
    "theirs", "them", "themselves", "then", "there", "there's", "these", "they",
    "they'd", "they'll", "they're", "they've", "this", "those", "through", "to",
    "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll",
    "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's",
    "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're",
    "you've", "your", "yours", "yourself", "yourselves"
    }


def tokenize(raw_words):
    '''
    Gets a list of words (raw_words) and tokenizes it
    Returns: dict of unique words : frequency (unique_word_counter)
    '''
    tokenized_words = []    # List of words after tokenized
    unique_word_counter = {}  # Manually count words using a dictionary

    # Eliminate stopwords
    for word in raw_words: 
        word = word.lower()
        cleaned_word = ''.join(char for char in word if char.isalnum())
        if cleaned_word and cleaned_word not in stopwords and len(cleaned_word) > 1:
            tokenized_words.append(cleaned_word)

    # Populate the unique_word_counter dict with unique words : frequency
    for word in tokenized_words:
        if word in unique_word_counter:
            unique_word_counter[word] += 1  # Increment count if word is already in dictionary
        else:
            unique_word_counter[word] = 1
    
    return unique_word_counter # will have all words not in stopwords



def create_report(json_files):
    '''
    Parameters: json_files = list of json file names
    Writes: To be implemented later
    Returns: Nothing, writes to files
    '''
    longest_page_info = ("", 0)     # Initial longest tuple (url, word count)
    subdomain_counter = {}          # Regular dictionary to count unique URLs per subdomain
    tokenized_words = {}            # Dict of unique words : freq maintained for all the pages combined
    
    url_highest_words = ("x", 0)
    page_count = 0
    
    # Iterates through each json file, populating our designated data structures
    for json_file in json_files: 
        # Grabbing and opening file
        file_path = os.path.join("tokens_by_subdomain", json_file)  # Full path to the file
        with open(file_path, 'r') as f: 
            json_data = json.load(f) 


            tokenized_word_count = 0
            
            keys = list(json_data.keys())  # Get all keys as a list
            subdomain_name = keys[1]  # Access the second key
            myData = json_data[subdomain_name] #gets the data for tokens
            dict_counter = 0
            for dictionary in myData:
                for url, words in dictionary.items():
                    dict_counter += 1
                    word_counter = 0
                
                    # Tokenize myData and update the main tokenized_words dictionary
                    file_token_counts = tokenize(words)  # Dictionary of word: frequency for the current file
                    
                    for word, count in file_token_counts.items():
                        tokenized_word_count += count
                        word_counter += count
                        if word in tokenized_words:
                            tokenized_words[word] += count
                        else:
                            tokenized_words[word] = count

                    if word_counter > url_highest_words[1]:
                        url_highest_words = (url, word_counter)
                    # Check for the longest page for the report
                    if tokenized_word_count > longest_page_info[1]:
                        longest_page_info = (json_file, tokenized_word_count)
                    page_count += 1
                    # Increment the count for the subdomain
                    if subdomain_name in subdomain_counter:
                        subdomain_counter[subdomain_name] += 1  # Increment if exists
                    else:
                        subdomain_counter[subdomain_name] = 1  # Start count if new
                        
                        
    # Num of unique pages
    
    print(f"\033[1m\033[4mUnique Pages:\033[0m\n{page_count}\n")

    # Longest Page
    print(f"\033[1m\033[4mLongest page:\033[0m \nURL : {url_highest_words[0]}\nWord Count : {url_highest_words[1]}")

    # Array of 50 most common words manually
    most_common_words = sorted(tokenized_words.items(), key=lambda x: x[1], reverse=True)[:50]
    print("\033[1m\033[4m\n50 Most Common Words:\033[0m")
    words = [t[0] for t in most_common_words]
    print(words)
  

    print("\033[1m\033[4m\nSubdomains in uci.edu:\033[0m")
    for subdomain, count in sorted(subdomain_counter.items()):
        print(f"{subdomain}, {count}")
    print()


def main():
    # Returns a list of all the files in the tokens_by_subdomain folder
    json_files = [f for f in os.listdir("tokens_by_subdomain") if f.endswith('.json')]
    create_report(json_files)

if __name__ == "__main__":
    main()
