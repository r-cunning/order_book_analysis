import requests
from bs4 import BeautifulSoup
import os
import time
from datetime import datetime, timedelta
import bz2

# Function to download a file from a specified URL
def download_file(folder_path='data/eve_ref_market_orders/latest',
                  url='https://data.everef.net/market-orders/'):
    """
    Downloads a file from the given URL and saves it to the specified folder.

    Parameters:
    - folder_path (str): The local directory where the file will be saved.
    - url (str): The URL of the file to download.

    Returns:
    - full_path (str): The full path of the downloaded file.
    """
    # Extract the file name from the URL
    local_filename = url.split('/')[-1]
    
    # Ensure the target folder exists
    os.makedirs(folder_path, exist_ok=True)
    
    # Construct the full file path for saving the file
    full_path = os.path.join(folder_path, local_filename)
    
    # Stream the download to efficiently handle large files
    with requests.get(url, stream=True) as r:
        r.raise_for_status()  # Ensure the download was successful
        # Write the downloaded content in chunks to avoid memory overload
        with open(full_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    
    return full_path


# Function to get the latest CSV files from the specified URL and download them
def get_latest(folder_path='data/eve_ref_market_orders/latest',
               url='https://data.everef.net/market-orders/'):
    """
    Fetches the latest CSV files from the provided URL and downloads them to the specified folder.

    Parameters:
    - folder_path (str): The local directory where the files will be saved.
    - url (str): The base URL from which to fetch and download the CSV files.
    """
    # Send an HTTP GET request to fetch the content of the webpage
    response = requests.get(url)
    response.raise_for_status()  # Ensure the request was successful

    # Parse the HTML content of the page
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all hyperlinks that point to CSV files compressed in bz2 format
    csv_links = soup.find_all('a', href=True)
    csv_urls = [link['href'] for link in csv_links if link['href'].endswith('.csv.bz2')]

    # Download each CSV file found on the page
    for csv_url in csv_urls:
        full_csv_url = requests.compat.urljoin(url, csv_url)
        print(f'Downloading {full_csv_url}')
        download_file(folder_path, full_csv_url)
    
    print('Download complete.')


# Function to download CSV files from the last two days
def get_two_day_window(folder_path='data/eve_ref_market_orders/last2days', 
                       base_url='https://data.everef.net/market-orders/history/'):
    """
    Fetches and downloads CSV files from the last two days from the specified base URL.

    Parameters:
    - folder_path (str): The local directory where the files will be saved.
    - base_url (str): The base URL for fetching historical market orders.
    """
    # Calculate the dates for the last two days
    today = datetime.now().date()
    last_two_days = [today - timedelta(days=i) for i in range(1, 3)]

    # Loop through each date in the last two days
    for date in last_two_days:
        # Format the URL path to include the year and date in YYYY/YYYY-MM-DD format
        url = f"{base_url}{date.year}/{date}/"
        
        # Send an HTTP GET request to fetch the content of the webpage for each day
        response = requests.get(url)
        response.raise_for_status()  # Ensure the request was successful

        # Parse the HTML content of the page
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all hyperlinks that point to CSV files compressed in bz2 format
        csv_links = soup.find_all('a', href=True)
        csv_urls = [link['href'] for link in csv_links if link['href'].endswith('.csv.bz2')]

        # Download each CSV file found for the specific date
        for csv_url in csv_urls:
            full_csv_url = requests.compat.urljoin(url, csv_url)
            print(f'Downloading {full_csv_url}')
            download_file(folder_path, full_csv_url)
    
    print('Download complete.')
    
    # Extract the downloaded .bz2 files and remove the original compressed files
    extract_bz2_files(folder_path)
    delete_bz2_files(folder_path)


# Function to update the latest market order book
def update_book(folder_path='data/eve_ref_market_orders/latest',
                url='https://data.everef.net/market-orders/'):
    """
    Updates the market order book by downloading the latest data, extracting the files, and deleting the compressed files.

    Parameters:
    - folder_path (str): The local directory where the files will be saved and processed.
    - url (str): The URL from which to fetch the latest market order data.
    """
    get_latest(folder_path, url)
    extract_bz2_files(folder_path)
    delete_bz2_files(folder_path)


# Function to extract .bz2 files
def extract_bz2_files(folder_path='data/eve_ref_market_orders/latest'):
    """
    Extracts all .bz2 compressed files in the specified folder.

    Parameters:
    - folder_path (str): The directory containing the .bz2 files to be extracted.
    """
    # Iterate through all files in the specified directory
    for file_name in os.listdir(folder_path):
        # Check if the file is a .bz2 compressed file
        if file_name.endswith('.bz2'):
            file_path = os.path.join(folder_path, file_name)
            output_file_path = os.path.splitext(file_path)[0]  # Remove the .bz2 extension to create the output file path

            # Extract the contents of the .bz2 file
            with bz2.BZ2File(file_path, 'rb') as file:
                with open(output_file_path, 'wb') as new_file:
                    for data in iter(lambda: file.read(100 * 1024), b''):
                        new_file.write(data)
            
            print(f'Extracted {file_path} to {output_file_path}')


# Function to delete .bz2 files after extraction
def delete_bz2_files(folder_path='data/eve_ref_market_orders/latest'):
    """
    Deletes all .bz2 compressed files in the specified folder.

    Parameters:
    - folder_path (str): The directory containing the .bz2 files to be deleted.
    """
    # Iterate through all files in the specified directory
    for file_name in os.listdir(folder_path):
        # Check if the file is a .bz2 compressed file
        if file_name.endswith('.bz2'):
            file_path = os.path.join(folder_path, file_name)
            os.remove(file_path)  # Delete the .bz2 file
            print(f'Deleted {file_path}')
