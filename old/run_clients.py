import threading
from old.client import send  # Assuming `send` is from `client.py`
from old.bidder import generate_max_bids, make_bid

# Number of clients to simulate
num_clients = 5

# Function to simulate client behavior
def run_client():
    client_max_bids = generate_max_bids(10)  # Each client has unique max bids for 10 items

    # Simulate bidding on items (assuming server broadcasts current prices)
    items = ["Item1", "Item2", "Item3", "Item4", "Item5", "Item6", "Item7", "Item8", "Item9", "Item10"]
    for item in items:
        current_price = 100  # Example current price, would typically come from the server
        bid = make_bid(item, current_price, client_max_bids)
        
        # If a bid is placed, send it to the server
        if bid is not None:
            send(f"{item}:{bid}")

# Start multiple client threads
threads = []
for _ in range(num_clients):
    client_thread = threading.Thread(target=run_client)
    threads.append(client_thread)
    client_thread.start()

# Join threads to ensure all clients complete their bidding
for thread in threads:
    thread.join()
