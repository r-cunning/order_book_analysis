import requests
from bs4 import BeautifulSoup
import os

import time
from datetime import datetime, timedelta

# Function to download a file from a URL
def download_file(folder_path = 'data/eve_ref_market_orders/latest',
               url = 'https://data.everef.net/market-orders/'):
    local_filename = url.split('/')[-1]
    # Create folder if it doesn't exist
    os.makedirs(folder_path, exist_ok=True)
    # Full path for saving the file
    full_path = os.path.join(folder_path, local_filename)
    # Stream the download to handle large files
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(full_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return full_path


def get_latest(folder_path = 'data/eve_ref_market_orders/latest',
               url = 'https://data.everef.net/market-orders/'):

    # Send a GET request to fetch the webpage content
    response = requests.get(url)
    response.raise_for_status()  # Check if the request was successful

    # Parse the webpage content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all links ending with .csv
    csv_links = soup.find_all('a', href=True)
    csv_urls = [link['href'] for link in csv_links if link['href'].endswith('.csv.bz2')]


    # Download each CSV file
    for csv_url in csv_urls:
        full_csv_url = requests.compat.urljoin(url, csv_url)
        print(f'Downloading {full_csv_url}')
        download_file(folder_path, full_csv_url)

    
    print('Download complete.')

def get_two_day_window(folder_path='data/eve_ref_market_orders/last2days', base_url='https://data.everef.net/market-orders/history/'):
    # Get today's date and the date of the day before yesterday
    today = datetime.now().date()
    last_two_days = [today - timedelta(days=i) for i in range(1, 3)]

    # Loop over the last two days
    for date in last_two_days:
        # Format the date in the URL as YYYY/YYYY-MM-DD/
        url = f"{base_url}{date.year}/{date}/"
        
        # Send a GET request to fetch the webpage content
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful

        # Parse the webpage content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all links ending with .csv.bz2
        csv_links = soup.find_all('a', href=True)
        csv_urls = [link['href'] for link in csv_links if link['href'].endswith('.csv.bz2')]

        # Download each CSV file
        for csv_url in csv_urls:
            full_csv_url = requests.compat.urljoin(url, csv_url)
            print(f'Downloading {full_csv_url}')
            download_file(folder_path, full_csv_url)
    
    print('Download complete.')
    extract_bz2_files(folder_path)
    delete_bz2_files(folder_path)
    
    
    
    

def update_book(folder_path = 'data/eve_ref_market_orders/latest',
               url = 'https://data.everef.net/market-orders/'):
    get_latest(folder_path, url)
    extract_bz2_files(folder_path)
    delete_bz2_files(folder_path)
    
    
import bz2

def extract_bz2_files(folder_path = 'data/eve_ref_market_orders/latest'):
    # List all files in the directory
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.bz2'):
            file_path = os.path.join(folder_path, file_name)
            output_file_path = os.path.splitext(file_path)[0]  # Remove .bz2 extension

            with bz2.BZ2File(file_path, 'rb') as file:
                with open(output_file_path, 'wb') as new_file:
                    for data in iter(lambda: file.read(100 * 1024), b''):
                        new_file.write(data)
                        
            
            print(f'Extracted {file_path} to {output_file_path}')

def delete_bz2_files(folder_path = 'data/eve_ref_market_orders/latest'):
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.bz2'):
            file_path = os.path.join(folder_path, file_name)
            os.remove(file_path)
            print(f'Deleted {file_path}')