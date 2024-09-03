import pandas as pd
import math
from datetime import datetime, timedelta

def check_competition(sell_orders, buy_orders):
    """
    Analyzes the competition in the market by counting the number of buy and sell orders 
    placed within specific time windows (3 hours and 24 hours) relative to the current time.

    Parameters:
    - sell_orders (DataFrame): DataFrame containing the current sell orders.
    - buy_orders (DataFrame): DataFrame containing the current buy orders.

    Returns:
    - competition (dict): Dictionary containing the count of buy and sell orders within the 
      3-hour and 24-hour windows.
    """

    # Initialize counters for buy and sell competition in both 3-hour and 24-hour windows
    buy_competition_3hr = 0
    buy_competition_24hr = 0
    sell_competition_3hr = 0
    sell_competition_24hr = 0
    
    # Get the current UTC time for comparison
    current_time = datetime.utcnow()

    # Loop through the buy orders to determine competition within the time windows
    for i in range(len(buy_orders)):
        # Convert the 'issued' timestamp from string format to a datetime object
        issued_time = datetime.strptime(buy_orders['issued'].iloc[i], '%Y-%m-%dT%H:%M:%SZ')
        
        # Increment the counter if the buy order was issued within the last 3 hours
        if current_time - issued_time <= timedelta(hours=3):
            buy_competition_3hr += 1
        
        # Increment the counter if the buy order was issued within the last 24 hours
        if current_time - issued_time <= timedelta(hours=24):
            buy_competition_24hr += 1
    
    # Loop through the sell orders to determine competition within the time windows
    for i in range(len(sell_orders)):
        # Convert the 'issued' timestamp from string format to a datetime object
        issued_time = datetime.strptime(sell_orders['issued'].iloc[i], '%Y-%m-%dT%H:%M:%SZ')
        
        # Increment the counter if the sell order was issued within the last 3 hours
        if current_time - issued_time <= timedelta(hours=3):
            sell_competition_3hr += 1
        
        # Increment the counter if the sell order was issued within the last 24 hours
        if current_time - issued_time <= timedelta(hours=24):
            sell_competition_24hr += 1
    
    # Store the competition metrics in a dictionary
    competition = {
        'buy_competition_3hr': buy_competition_3hr,
        'buy_competition_24hr': buy_competition_24hr,
        'sell_competition_3hr': sell_competition_3hr,
        'sell_competition_24hr': sell_competition_24hr
    }
    
    return competition


def scan(orders, type_id, station_id, sell_spread_threshold=0.5, profit_margin=0, cost_threshold=math.inf):
    """
    Analyzes market orders to identify potential trading opportunities (snipes).
    
    A snipe occurs when there is a significant difference between the lowest sell price and the highest buy price,
    allowing for a potential quick profit by buying low and selling high.

    Parameters:
    - orders (DataFrame): DataFrame containing market orders for a specific type and station.
    - type_id (int): The ID of the item type being analyzed.
    - station_id (int): The ID of the station where the orders are located.
    - sell_spread_threshold (float, optional): Threshold to identify a snipe based on the difference between 
      the lowest and second lowest sell prices (default is 0.5).
    - profit_margin (float, optional): Minimum profit required to consider a snipe (default is 0).
    - cost_threshold (float, optional): Maximum cost allowed for considering a snipe (default is infinity).

    Returns:
    - trade_dict (dict): Dictionary containing details of the snipe if found, otherwise returns an empty dictionary.
    """

    # Initialize snipe status and trade details dictionary
    snipe_found = False
    trade_dict = {}

    # Filter and sort orders by price for analysis
    sell_orders = orders[orders['is_buy_order'] == False].sort_values(by='price', ascending=True)
    buy_orders = orders[orders['is_buy_order'] == True].sort_values(by='price', ascending=False)

    # If there are no buy or sell orders, return False indicating no snipes found
    if sell_orders.empty or buy_orders.empty:
        return False  
    
    # Determine the lowest sell price and volume
    lowest_sell_price = sell_orders['price'].min()
    lowest_sell_volume = sell_orders['volume_remain'].iloc[0]
    
    # Determine the second lowest sell price, if only one sell order exists, use the lowest sell price
    if len(sell_orders) == 1:
        second_lowest_sell_price = lowest_sell_price
    else:
        second_lowest_sell_price = sell_orders['price'].iloc[1]
    
    # Determine the highest buy price
    highest_buy_price = buy_orders['price'].max()

    # Calculate the spread between the highest buy price and the lowest sell price
    spread = abs(highest_buy_price - lowest_sell_price)
    # Calculate the difference between the lowest sell price and the second lowest sell price
    difference_to_next_sell = abs(second_lowest_sell_price - lowest_sell_price)

    # Calculate the profit margin by reselling at the second lowest sell price
    margin = second_lowest_sell_price - lowest_sell_price
    profit = margin * lowest_sell_volume
    
    # Calculate the total cost for purchasing all units at the lowest sell price
    cost = lowest_sell_price * lowest_sell_volume
    
    # Determine the cost-profit ratio
    cost_profit_ratio = profit / cost
    
    # Check the competition within the time windows
    competition = check_competition(sell_orders, buy_orders)
    
    # Determine if a snipe is found based on the spread, profit, and cost conditions
    if (spread < (difference_to_next_sell * sell_spread_threshold) and 
        profit > profit_margin and 
        cost < cost_threshold) or (lowest_sell_price == highest_buy_price and 
        profit > profit_margin and 
        cost < cost_threshold):

        # Populate the trade details dictionary with relevant data
        trade_dict['type_id'] = type_id
        trade_dict['station_id'] = station_id
        trade_dict['profit'] = profit
        trade_dict['opportunity_cost'] = cost
        trade_dict['cost_profit_ratio'] = cost_profit_ratio
        trade_dict['sell_depth'] = len(sell_orders)
        trade_dict['buy_depth'] = len(buy_orders)
        trade_dict['buy_competition_3hr'] = competition['buy_competition_3hr']
        trade_dict['buy_competition_24hr'] = competition['buy_competition_24hr']
        trade_dict['sell_competition_3hr'] = competition['sell_competition_3hr']
        trade_dict['sell_competition_24hr'] = competition['sell_competition_24hr']
        
        # Output detailed information about the snipe opportunity
        print("--------------------------------------------------------------------------")
        print(f"Type ID {type_id} is a snipe at station: {station_id}.") 
        print(f"Profit: {profit} ISK || Cost: {cost} ISK")
        print(f"Lowest sell: {lowest_sell_price} Highest buy: {highest_buy_price} volume: {lowest_sell_volume}") 
        print(f"Second sell: {second_lowest_sell_price} ~ Margin: {margin} ISK")
        print(f"Sell depth: {len(sell_orders)} Buy depth: {len(buy_orders)}")
        print(f"Buy Competition (3hr): {competition['buy_competition_3hr']} (24hr): {competition['buy_competition_24hr']}")
        print(f"Sell Competition (3hr): {competition['sell_competition_3hr']} (24hr): {competition['sell_competition_24hr']}")
        print("--------------------------------------------------------------------------")
                        
        return trade_dict
    else:
        # If no snipe found, return an empty dictionary
        return trade_dict


def filter_data(data, station_id, sell_spread_threshold=0.8, profit_margin=0, cost_threshold=math.inf):
    """
    Filters and analyzes market data for a specific station to identify potential snipes across all item types.

    Parameters:
    - data (DataFrame): DataFrame containing market orders.
    - station_id (int): The ID of the station where the orders are located.
    - sell_spread_threshold (float, optional): Threshold to identify a snipe based on the difference between 
      the lowest and second lowest sell prices (default is 0.8).
    - profit_margin (float, optional): Minimum profit required to consider a snipe (default is 0).
    - cost_threshold (float, optional): Maximum cost allowed for considering a snipe (default is infinity).

    Returns:
    - snipes (list): A list of dictionaries containing details of all identified snipes.
    """

    # Filter data for the specified station
    station_data = data[data['location_id'] == station_id]
    
    # Initialize a list to store detected snipes
    snipes = []
    
    # Get unique type IDs to analyze each item type individually
    type_ids = data['type_id'].unique()
    
    # Iterate over each item type to analyze market orders
    for type_id in type_ids:
        orders = station_data[station_data['type_id'] == type_id]
        snipe_dict = scan(orders, type_id, station_id, sell_spread_threshold=sell_spread_threshold, 
                          profit_margin=profit_margin, cost_threshold=cost_threshold)
        
        # If a snipe is found, add it to the list of snipes
        if not snipe_dict:
            continue
        else: 
            snipes.append(snipe_dict)
    
    # If no snipes are found, print a message and return an empty list
    if not snipes:
        print("          No snipes found. Back to sleep.")
        print("==========================================")
    
    return snipes
