import asyncio
import json
import websockets
from old.bidder import make_bid, generate_max_bids

ADDR = 'ws://localhost:5050'
DISCONNECT_MESSAGE = "!DISCONNECT"

# Example for a client with randomized max bids
client_max_bids = generate_max_bids(10)  # Generates max bids for 10 items

# Example usage

async def Start():
    async with websockets.connect(ADDR) as websocket:
        print(await websocket.recv())
        item = "Item1"
        current_price = 100
        bidAmount = make_bid(item, current_price, client_max_bids)

        if bidAmount is not None:
            bid = json.dumps({"item":item, "bidAmount":bidAmount})
            print(f"[OUTBOUND] {bid}")
            await websocket.send(bid)
            await websocket.send(DISCONNECT_MESSAGE)

asyncio.run(Start())