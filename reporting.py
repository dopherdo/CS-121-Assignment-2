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

def create_report(json_files):
    longest_page_info = ("", 0)  # (filename, word count)
    word_counter = {}  # Manually count words using a dictionary
    subdomain_counter = {}  # Regular dictionary to count unique URLs per subdomain



    # TODO: TOKENIZE HERE


    for json_file in json_files:
        with open(json_file, 'r') as f:
            json_data = json.load(f)
            word_count = 0

            # Update word frequency manually
            for subdomain, tokens in json_data.items():
                # counts the number of words
                word_count = len(tokens)
                word = word.lower()  # Convert to lower case for case insensitivity
                if word not in stopwords:
                    if word in word_counter:
                        word_counter[word] += 1
                    else:
                        word_counter[word] = 1

            # Check for the longest page for the report
            if word_count > longest_page_info[1]:
                longest_page_info = (json_file, word_count)

            # Increment the count for the subdomain
                if subdomain in subdomain_counter:
                    subdomain_counter[subdomain] += 1  # Increment if exists
                else:
                    subdomain_counter[subdomain] = 1  # Start count if new

    # Prepare the report results
    longest_page_filename, longest_page_word_count = longest_page_info
    
    # Get the 50 most common words manually
    most_common_words = sorted(word_counter.items(), key=lambda x: x[1], reverse=True)[:50]
    
    subdomain_report = {subdomain: len(urls) for subdomain, urls in subdomain_counter.items()}

    # Output the report
    print(f"Longest page: {longest_page_filename} with {longest_page_word_count} words")
    print("\n50 Most Common Words:")
    for word, count in most_common_words:
        print(f"{word}: {count}")

    print("\nSubdomains in uci.edu:")
    for subdomain, count in sorted(subdomain_report.items()):
        print(f"{subdomain}, {count}")

def main():
    # Replace this with the actual path to your JSON files
    json_files = [f for f in os.listdir('"tokens_by_subdomain"') if f.endswith('.json')]
    create_report(json_files)

if __name__ == "__main__":
    main()
