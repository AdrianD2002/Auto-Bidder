import random
"""
This is the current structure of the client_max_bid dictionary:
client_max_bids = {
    "Item1": 120,
    "Item2": 50,
    "Item3": 320,
    "Item4": 75,
    "Item5": 200,
    "Item6": 150,
    "Item7": 400,
    "Item8": 90,
    "Item9": 350,
    "Item10": 180
}
"""
def generate_max_bids(num_items):
    """Generate a dictionary of randomized max bids for each item."""
    return {f"Item{i+1}": random.randint(50, 500) for i in range(num_items)}

def make_bid(item, current_price, client_max_bids):
    """
    Determine if a client will bid on an item and return the bid amount.
    """
    max_bid = client_max_bids.get(item)
    if max_bid is None:
        return None  # Item not in client's preferences

    # 30% chance of skipping bid
    if random.random() < 0.3:
        print(f"Client skips bidding on {item} this round.")
        return None

    # Place bid if current price is below max bid
    if current_price < max_bid:
        new_bid = current_price + random.randint(1, 10)  # Increase bid slightly
        print(f"Client bids ${new_bid} on {item} (current price: ${current_price})")
        return new_bid
    else:
        print(f"No bid: Client's max bid for {item} is ${max_bid}.")
        return None
