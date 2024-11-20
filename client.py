import socket
from bidder import make_bid, generate_max_bids

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "" # <- put public address of server machine here
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)

    send_length = str(msg_length).encode(FORMAT)
    send_length += b" " * (HEADER - len(send_length))

    client.send(send_length)
    client.send(message)

    print(client.recv(2048).decode(FORMAT))


# Example for a client with randomized max bids
client_max_bids = generate_max_bids(10)  # Generates max bids for 10 items

# Example usage
item = "Item1"
current_price = 100
bid = make_bid(item, current_price, client_max_bids)

if bid is not None:
    send(f"{item}:{bid}")


send("Hello World!")
send(DISCONNECT_MESSAGE)