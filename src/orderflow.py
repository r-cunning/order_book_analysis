import numpy as np
import pandas as pd
import os
import re

# Implementation of Kolm et al. 2021
# Kolm PN, Turiel J, Westray N. Deep Order Flow Imbalance: Extracting Alpha at Multiple Horizons from the Limit Order Book [Internet]. Rochester, NY; 2021 [cited 2024 Jul 26]. Available from: https://papers.ssrn.com/abstract=3900141



import numpy as np
import os
import re
import pandas as pd

def bid_orderflow(buy_state0, buy_state1):
    """
    Calculates the bid order flow between two consecutive states (time points).

    Bid order flow measures the change in the volume of buy orders between two states.
    Positive values indicate an increase in buy orders, while negative values indicate a decrease.

    Parameters:
    - buy_state0 (DataFrame): Initial state of the buy orders. Contains columns 'price' and 'volume_remain'.
    - buy_state1 (DataFrame): State of the buy orders after a market event. Contains columns 'price' and 'volume_remain'.

    Returns:
    - bOF_array (ndarray): Array of bid order flow values for each price level.
    """
    bOF_list = []  # List to store bid order flow values

    for i in range(len(buy_state0)):
        # Case 1: The price increased
        if buy_state1['price'].iloc[i] > buy_state0['price'].iloc[i]:
            bOF = buy_state1['volume_remain'].iloc[i]
            bOF_list.append(bOF)
        # Case 2: The price remained the same
        elif buy_state1['price'].iloc[i] == buy_state0['price'].iloc[i]:
            bOF = buy_state1['volume_remain'].iloc[i] - buy_state0['volume_remain'].iloc[i]
            bOF_list.append(bOF)
        # Case 3: The price decreased
        elif buy_state1['price'].iloc[i] < buy_state0['price'].iloc[i]:
            bOF = -buy_state1['volume_remain'].iloc[i]
            bOF_list.append(bOF)
    
    bOF_array = np.array(bOF_list)  # Convert list to numpy array
    return bOF_array


def ask_orderflow(sell_state0, sell_state1):
    """
    Calculates the ask order flow between two consecutive states (time points).

    Ask order flow measures the change in the volume of sell orders between two states.
    Positive values indicate an increase in sell orders, while negative values indicate a decrease.

    Parameters:
    - sell_state0 (DataFrame): Initial state of the sell orders. Contains columns 'price' and 'volume_remain'.
    - sell_state1 (DataFrame): State of the sell orders after a market event. Contains columns 'price' and 'volume_remain'.

    Returns:
    - aOF_array (ndarray): Array of ask order flow values for each price level.
    """
    aOF_list = []  # List to store ask order flow values

    for i in range(len(sell_state0)):
        # Case 1: The price increased
        if sell_state1['price'].iloc[i] > sell_state0['price'].iloc[i]:
            aOF = -sell_state1['volume_remain'].iloc[i]
            aOF_list.append(aOF)
        # Case 2: The price remained the same
        elif sell_state1['price'].iloc[i] == sell_state0['price'].iloc[i]:
            aOF = sell_state1['volume_remain'].iloc[i] - sell_state0['volume_remain'].iloc[i]
            aOF_list.append(aOF)
        # Case 3: The price decreased
        elif sell_state1['price'].iloc[i] < sell_state0['price'].iloc[i]:
            aOF = sell_state1['volume_remain'].iloc[i]
            aOF_list.append(aOF)
    
    aOF_array = np.array(aOF_list)  # Convert list to numpy array
    return aOF_array


def calc_feats(buy_state0, buy_state1, sell_state0, sell_state1, date=None):
    """
    Calculates key features related to market order flow and price movement.

    This function computes the bid order flow, ask order flow, and mid-price return between two states.

    Parameters:
    - buy_state0 (DataFrame): Initial state of the buy orders.
    - buy_state1 (DataFrame): State of the buy orders after a market event.
    - sell_state0 (DataFrame): Initial state of the sell orders.
    - sell_state1 (DataFrame): State of the sell orders after a market event.
    - date (optional): The date associated with the states (not used in the computation).

    Returns:
    - dict: A dictionary containing the following key:
        - 'mid_price_return' (float): The difference in the mid-price between the two states.
    """
    # Calculate bid and ask order flow
    bOF = bid_orderflow(buy_state0, buy_state1)
    aOF = ask_orderflow(sell_state0, sell_state1)
    
    # Calculate the mid-price for the initial and final states
    mid_price0 = (buy_state0['price'].iloc[0] + sell_state0['price'].iloc[0]) / 2
    mid_price1 = (buy_state1['price'].iloc[0] + sell_state1['price'].iloc[0]) / 2
    
    # Calculate the mid-price return (price movement)
    mid_price_return = mid_price1 - mid_price0

    return {
        'mid_price_return': mid_price_return,  # Return the mid-price return
    }


def load_data(data, type_id, station_id=60003760, rows=10):
    """
    Filters and loads buy and sell order data from a DataFrame.

    This function selects buy and sell orders for a specific type of item within a given station,
    and returns the top `rows` orders sorted by price.

    Parameters:
    - data (DataFrame): The original dataset containing market orders.
    - type_id (int): The ID of the item type to filter.
    - station_id (int, optional): The station ID to filter (default is 60003760).
    - rows (int, optional): The number of top orders to select (default is 10).

    Returns:
    - dict: A dictionary containing:
        - 'buy_data' (DataFrame): The top buy orders sorted by price (descending).
        - 'sell_data' (DataFrame): The top sell orders sorted by price (ascending).
    """
    # Filter data for the specified station
    data = data[data['station_id'] == station_id]
    
    # Select and sort the top `rows` sell orders by price (ascending)
    sell_data = data[(data['type_id'] == type_id) & (data['is_buy_order'] == False)].sort_values('price', ascending=True).head(rows).drop(columns=['constellation_id', 'region_id', 'http_last_modified', 'system_id', 'location_id', 'station_id'])
    
    # Select and sort the top `rows` buy orders by price (descending)
    buy_data = data[(data['type_id'] == type_id) & (data['is_buy_order'] == True)].sort_values('price', descending=True).head(rows).drop(columns=['constellation_id', 'region_id', 'http_last_modified', 'system_id', 'location_id', 'station_id'])
    
    return {'buy_data': buy_data, 'sell_data': sell_data}  # Return the filtered buy and sell data


def process_csv_files(folder_path, type_id, station_id=60003760, horizon=10):
    """
    Processes multiple CSV files in a directory, extracting market order data for analysis.

    This function reads CSV files from the specified directory, filters them based on the item type and station,
    and stores the top `horizon` buy and sell orders from each file.

    Parameters:
    - folder_path (str): Path to the directory containing the CSV files.
    - type_id (int): The ID of the item type to filter.
    - station_id (int, optional): The station ID to filter (default is 60003760).
    - horizon (int, optional): The number of top orders to select from each file (default is 10).

    Returns:
    - data_dict (dict): A dictionary where the keys are timestamps (extracted from filenames) and the values
      are dictionaries containing 'buy_data' and 'sell_data' DataFrames.
    """
    data_dict = {}  # Initialize an empty dictionary to store data

    for file_name in os.listdir(folder_path):
        if file_name.endswith('.csv'):  # Process only CSV files
            # Extract the timestamp from the filename using regex
            match = re.search(r'market-orders-(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.v3\.csv', file_name)
            if match:
                key = match.group(1)  # Use the timestamp as the dictionary key
                file_path = os.path.join(folder_path, file_name)  # Construct full file path
                df = pd.read_csv(file_path)  # Read the CSV file into a DataFrame
                
                # Filter the DataFrame for the specified type ID
                filtered_df = df[df['type_id'] == type_id]
                
                # Load the filtered data into buy_data and sell_data
                data = load_data(filtered_df, type_id=type_id, station_id=station_id, rows=horizon)
                
                # Store the buy and sell data in the dictionary under the extracted timestamp
                data_dict[key] = {'buy_data': data['buy_data'], 'sell_data': data['sell_data']}
                
    return data_dict  # Return the dictionary containing processed data for all files
