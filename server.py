
import asyncio
import json
import pprint
import random
import websockets

###########################################
###########################################
###########################################
###########################################
#                   Styling Guidlines:
# For functions: use capital letters for the first letter of each word. ex: NameFunc().
# For variables: use standard camel case. ex: nameVar.
###########################################
###########################################
###########################################
###########################################

PORT = 5050
DISCONNECT_MESSAGE = "!DISCONNECT"

connectedClients = set() # Set of currently connected clients
auctionItems = []

async def InventoryGenerator():
    items = {}

    for i in range(random.randint(10, 20)): # Sets range of number of items from 10 to 20.
        itemName = f"Item_{i + 1}" # What item number being displayed.
        
        initialPrice = random.randint(50, 500) # Set random initial price between 50 and 500.

        initialUnits = random.randint(15, 150) # Set random  initial units between 15 and 150.
        
        items[itemName] = { # Dictionary for all items, their price and units associated.
            "price": initialPrice,
            "units": initialUnits
        }
        
    pprint.pprint(items)
    return items

async def BroadcastItems(itemName, itemDetail):
    auctionState = {
        "type": "auctionState",
        "items": [
            {"name": itemName, "price": details["initialPrice"], "units": details["initialUnits"]}
            for itemName, details in auctionItems.items()
        ]
    }
    msg = json.dumps(auctionState)
    if connectedClients:
        await asyncio.wait([client.send(msg) for client in connectedClients])
    print("[BROADCAST] Current auction state is sent to all clients")
    
async def UpdateBroadcast():
    while True:
        await BroadcastItems("", auctionItems)
        await asyncio.sleep(1)
"""
Updating Bids:

    When a bid is received, check if its higher than the current price for the item.
    If the bid is valid and there are units left, update the items price and decrement the unit count.

"""    

async def HandleBid(websocket, item, bidAmount):                       # Switched to using guard clauses for readability
                                                                        
    if not item in auctionItems:
        print("[ERROR] Item does not exist")
        nonexistent = json.dumps({"response":"nonexistent"})
        await websocket.send(nonexistent)

    if auctionItems[item]["units"] <= 0:
        print("[ERROR] Item out of stock")
        unavailable = json.dumps({"response":"unavailable"})
        await websocket.send(unavailable)

    if bidAmount <= auctionItems[item]["price"]:
        print("[REJECTED] Bid not beat current price")
        rejected = json.dumps({"response":"rejected"})
        await websocket.send(rejected)

    # If the code reaches this point, then the bid is valid

    print(f"[ACCEPTED] Bid on {item} accepted for {bidAmount}")
    auctionItems[item]["price"] = bidAmount                        # Update to new highest bid
    auctionItems[item]["units"] -= 1                                # Decrease available units
    accepted = json.dumps({"response":"accepted"})
    await websocket.send(accepted)
    await BroadcastItems(item, auctionItems[item])

async def HandleNewClient(websocket):
    try:
        connectedClients.add(websocket)                     # Add new client to set of connections
        print(f"[CONNECT] New connection: {websocket}")
        await websocket.send("[SERVER] Welcome to the Bid!")
        
        async for msg in websocket:
            if msg == DISCONNECT_MESSAGE:
                connectedClients.remove(websocket)
                print(f"[DISCONNECT] Client closed connection: {websocket}")
                return
            
            rcvdJson = json.loads(msg)
            item = rcvdJson["item"]
            bidAmount = rcvdJson["bid_amount"]
            await HandleBid(websocket, item, bidAmount)

    except websockets.exceptions.ConnectionClosed: # Connection closed unexpectedly
        print(f"[DISCONNECT] Client disconnected unexpectedly: {websocket}")
        connectedClients.remove(websocket)

    finally:
        print(f"[DISCONNECT] Cleaned up connection: {websocket}")
        connectedClients.remove(websocket)

async def StartServer():
    auctionItems = await InventoryGenerator()
    async with websockets.serve(HandleNewClient, '0.0.0.0', PORT) as server:
        print(f"[LISTENING] Server listening on port {PORT}")
        await server.serve_forever()

print("[STARTING]")
asyncio.run(StartServer())