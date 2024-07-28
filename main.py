import os
import re
import unicodedata
import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL of the Goodreads shelf
url = 'https://www.goodreads.com/shelf/show/relationship-self-help'

# Headers to mimic a real browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
}

# Number of top books to retrieve
top_n = 20  # Change this value to the number of top books you want to retrieve

# Send a request to the website
response = requests.get(url, headers=headers)

soup = BeautifulSoup(response.content, 'html.parser')

books = soup.select('#bodycontainer .elementList')

# Initialize lists to store the data
titles = []
ratings = []
num_ratings = []

# Function to clean unwanted characters from title
def clean_title(title):
    # Normalize unicode characters
    title = unicodedata.normalize('NFKD', title)
    # Replace replacement characters and non-printable characters with a space
    title = re.sub(r'[�]', ' ', title)
    title = re.sub(r'[^\x20-\x7E]', ' ', title)
    # Replace multiple spaces with a single space
    title = re.sub(r'\s+', ' ', title)
    return title.strip()

# Extract information for each book
for book in books:
    title_elem = book.select_one('a.bookTitle')
    author_elem = book.select_one('a.authorName')
    rating_text_elem = book.select_one('span.greyText.smallText')

    # Skip the book if any of the required elements are missing
    if title_elem is None or author_elem is None or rating_text_elem is None:
        continue

    title = title_elem.text.strip()
    author = author_elem.text.strip()
    rating_text = rating_text_elem.text.strip()
    # Clean the title
    title = clean_title(title)

    # Split the rating_text into a list
    parts = rating_text.split()
    
    # Initialize default values
    rating = "N/A"
    num_rating = "0"

    # Extract rating and number of ratings
    if len(parts) >= 5:
        try:
            rating = parts[2]
            num_rating = parts[4].replace(',', '')
        except ValueError:
            pass
    
    titles.append(title)
    ratings.append(float(rating) if rating != "N/A" else None)
    num_ratings.append(int(num_rating) if num_rating != "0" else 0)

# Create a DataFrame to store the data
df = pd.DataFrame({
    'Title': titles,
    'Rating': ratings,
    'Num Ratings': num_ratings
})

df.dropna(subset=['Rating'], inplace=True)
df.sort_values(by=['Num Ratings', 'Rating'], ascending=[False, False], inplace=True)

# Reset the index
df.reset_index(drop=True, inplace=True)

# Limit the number of top books
df = df.head(top_n)

# Calculate column widths
title_width = df['Title'].apply(len).max() + 2
rating_width = df['Rating'].apply(lambda x: len('{:.2f}'.format(x))).max() + 2
num_ratings_width = df['Num Ratings'].apply(lambda x: len(str(x))).max() + 2

# Path to the output file in the same directory as the script
file_path = 'books_data.txt'

# Delete the file if it exists
if os.path.exists(file_path):
    os.remove(file_path)

# Write the DataFrame to a text file with proper formatting
with open(file_path, 'w') as file:
    header = (
        'Title'.ljust(title_width) +
        'Rating'.ljust(rating_width) +
        'Num Ratings'.ljust(num_ratings_width)
    )
    file.write(header + '\n')
    file.write('-' * len(header) + '\n')
    
    for _, row in df.iterrows():
        line = (
            row['Title'].ljust(title_width) +
            '{:.2f}'.format(row['Rating']).ljust(rating_width) +
            str(row['Num Ratings']).ljust(num_ratings_width)
        )
        file.write(line + '\n')

print(f"Data for the top {top_n} books has been written to 'books_data.txt'.")
