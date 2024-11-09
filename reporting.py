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
    
    print(f"Word Count: {len(raw_words)}    |    Tokenized Word Count: {len(tokenized_words)}    |    Unique Word Count: {len(unique_word_counter.items())}\n")
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

            
            # Tokenize myData and update the main tokenized_words dictionary
            print(f"Tokenizing for {subdomain_name}")
            file_token_counts = tokenize(myData)  # Dictionary of word: frequency for the current file
            
            for word, count in file_token_counts.items():
                tokenized_word_count += count
                if word in tokenized_words:
                    tokenized_words[word] += count
                else:
                    tokenized_words[word] = count

                
            # Check for the longest page for the report
            if tokenized_word_count > longest_page_info[1]:
                longest_page_info = (json_file, tokenized_word_count)

            # Increment the count for the subdomain
                if subdomain_name in subdomain_counter:
                    subdomain_counter[subdomain_name] += 1  # Increment if exists
                else:
                    subdomain_counter[subdomain_name] = 1  # Start count if new


    # Longest Page
    longest_page_filename, longest_page_word_count = longest_page_info
    print(f"Longest page: {longest_page_filename} with {longest_page_word_count} words")

    # Array of 50 most common words manually
    most_common_words = sorted(tokenized_words.items(), key=lambda x: x[1], reverse=True)[:50]
    print("\n50 Most Common Words:")
    for word, count in most_common_words:
        print(f"{word}: {count}")

    print("\nSubdomains in uci.edu:")
    for subdomain, count in sorted(subdomain_counter.items()):
        print(f"{subdomain}, {count}")


def main():
    # Returns a list of all the files in the tokens_by_subdomain folder
    json_files = [f for f in os.listdir("tokens_by_subdomain") if f.endswith('.json')]
    create_report(json_files)

if __name__ == "__main__":
    main()
