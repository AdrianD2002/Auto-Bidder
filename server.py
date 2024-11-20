import socket
import threading

HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname()) # Get the IP of current machine
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

auctionItems = {
    "Item1": {"price": 100, "units": 20},
    "Item2": {"price": 200, "units": 15},
    "Item3": {"price": 250, "units": 18},
    "Item4": {"price": 50, "units": 24},
    "Item5": {"price": 175, "units": 24},
    "Item6": {"price": 340, "units": 16},
    "Item7": {"price": 110, "units": 31},
    "Item8": {"price": 210, "units": 12},
    "Item9": {"price": 200, "units": 6},
    "Item10": {"price": 160, "units": 40},
}
"""
Updating Bids:

    When a bid is received, check if its higher than the current price for the item.
    If the bid is valid and there are units left, update the items price and decrement the unit count.

"""
def handle_bid(item, bid_amount):
    if item in auctionItems and auctionItems[item]["units"] > 0:
        if bid_amount > auctionItems[item]["price"]:
            auctionItems[item]["price"] = bid_amount  # Update to new highest bid
            auctionItems[item]["units"] -= 1          # Decrease available units
            return True  # Bid accepted
    return False  # Bid rejected or item out of stock

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create socket
server.bind(ADDR)

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected")

    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)

            if msg == DISCONNECT_MESSAGE:
                connected = False

            print(f"[{addr}] {msg}")
            conn.send("Message Received".encode(FORMAT))

    conn.close()
    

def start():
    server.listen() # Listen for new connections
    print(f"[LISTENING] Listening on {SERVER}")
    while True:
        # Store connection and socket to communicate back
        conn, addr = server.accept() 

        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

print("[STARTING]")
start()