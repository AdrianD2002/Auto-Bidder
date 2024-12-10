import asyncio
import json
import pprint
import random
import websockets
import asyncio

#############################################################################################
## Styling Guidlines:                                                                      ##
## - For functions: use capital letters for the first letter of each word. ex: NameFunc(). ##
## - For variables: use standard camel case. ex: nameVar.                                  ##
#############################################################################################

########################################### Constants/Globals

PORT = 5050
DISCONNECT_MESSAGE = "!DISCONNECT"

connectedClients = set() # Set of currently connected clients

auctionItems = {}
initialPrices = {}
listCurrBids = []            # List of winning bids per round (resets every round, gets sorted by max bid)

########################################### Server<->Client Communication

async def BroadcastItems():
    message = {"type":"auctionState", "items": auctionItems}

    for websocket in connectedClients:
        await websocket.send(json.dumps(message))

    print("[BROADCAST] Current auction state sent to all clients")

async def HandleBid(websocket, item, bidAmount):                                        
    if not item in auctionItems:
        print("[ERROR] Item does not exist")
        nonexistent = json.dumps({"type":"bidResult", "response":"nonexistent"})
        await websocket.send(nonexistent)
        return

    if auctionItems[item]["units"] <= 0:
        print("[ERROR] Item out of stock")
        unavailable = json.dumps({"type":"bidResult", "response":"unavailable"})
        await websocket.send(unavailable)
        return

    if bidAmount <= auctionItems[item]["price"]:
        print("[REJECTED] Bid not beat current price")
        rejected = json.dumps({"type":"bidResult", "response":"rejected"})
        await websocket.send(rejected)
        return

    ### If the code reaches this point, then the bid is valid ###

    print(f"[ACCEPTED] Bid on {item} accepted for {bidAmount}")

    auctionItems[item]["price"] = bidAmount                                         # Update to new highest bid

    global listCurrBids
    listCurrBids.append({"bidder": websocket, "item": item, "bidAmount": bidAmount})    # Add winning bid to list of bids

    accepted = json.dumps({"type":"bidResult", "response":"accepted"})          # Notify bidder about win
    await websocket.send(accepted)

    await BroadcastItems()                              # Update all clients about current bid state

async def HandleNewClient(websocket):
    try:
        connectedClients.add(websocket)                     # Add new client to set of connections

        print(f"[CONNECT] New connection: {websocket.remote_address}")

        message = {"type":"auctionState", "items": auctionItems}

        await websocket.send(json.dumps(message))
        
        async for msg in websocket:
            if msg == DISCONNECT_MESSAGE:
                connectedClients.discard(websocket)
                print(f"[DISCONNECT] Client closed connection: {websocket.remote_address}")
                return
            
            #print(f'[RECEIVED] {msg}')
            rcvdJson = json.loads(msg)
            item = rcvdJson["item"]
            bidAmount = rcvdJson["bid_amount"]
            await HandleBid(websocket, item, bidAmount)

    except websockets.exceptions.ConnectionClosed: # Connection closed unexpectedly
        print(f"[DISCONNECT] Client disconnected unexpectedly: {websocket.remote_address}")
        connectedClients.discard(websocket)

    finally:
        print(f"[DISCONNECT] Cleaned up connection: {websocket.remote_address}")
        connectedClients.discard(websocket)

########################################### Auction Management

async def ManageAuction():
    global auctionItems
    global initialPrices

    print("[AUCTION] Auction process has started.")
    
    while True:

        # Check if there are any items left to auction
        activeItems = False
        for item in auctionItems:
            if auctionItems[item]["units"] > 0:
                activeItems = True
        if not activeItems:
            print("[AUCTION END] All items have been sold. Auction is now closed.")
            await AnnounceFinalStatus()
            break

        # Reset prices to original
        for item in auctionItems:
            #print(f'Reseting {item} from {auctionItems[item]["price"]} to {initialPrices[item]["price"]}')
            auctionItems[item]["price"] = initialPrices[item]["price"]

        message = {"type":"newRound", "items": auctionItems}
    
        for websocket in connectedClients:
            await websocket.send(json.dumps(message))

        print("[AUCTION ROUND] A new bidding round is starting.")

        await asyncio.sleep(5)

        # Simulate the selection of winners for items with bids
        await DecideWinner()

        # Broadcast updated auction state to all clients
        #await NotifyClients()

        print("[AUCTION ROUND] Bidding round completed.")

        await asyncio.sleep(5) # Allow 10 seconds in between rounds

async def DecideWinner():
    print("[DECIDING WINNERS] Starting winner selection process")

    global listCurrBids
    listBids = sorted(listCurrBids, key=lambda x: x["bidAmount"], reverse=True)         # Sort current bids by descending order of bid amount

    #pprint.pprint(listBids)

    wonItems = [] # list to keep track of items that were won in the bid (used to ignore losing bids)

    for bid in listBids:
        if bid["item"] in wonItems: # Item was already accounted for; skip
            continue
        
        global auctionItems
        wonItem = bid["item"]
        auctionItems[wonItem]["units"] = auctionItems[wonItem]["units"] - 1
        wonItems.append(bid["item"])

        winner = bid["bidder"]
        print(f"[WINNER] Rewarding {wonItem} to client {winner.remote_address}")

        await winner.send(json.dumps({"type":"rewardedItem","item":wonItem}))

    message = {"type":"updateQuantities", "items": auctionItems}

    for websocket in connectedClients:
        await websocket.send(json.dumps(message))

    listCurrBids = []

async def AnnounceFinalStatus():
    print("[FINAL STATUS] Announcing final status of the auction.")

    pprint.pprint(auctionItems)

    message = {"type":"auctionOver", "items": auctionItems}

    for websocket in connectedClients:
        await websocket.send(json.dumps(message))

########################################### Server Initialization

async def InventoryGenerator():
    print("[INVGEN] Generating Inventory:")
    global auctionItems
    global initialPrices

    for i in range(random.randint(5, 10)): # Sets range of number of items from 10 to 20.
        itemName = f"Item_{i + 1}" # What item number being displayed.
        
        initialPrice = random.randint(50, 500) # Set random initial price between 50 and 500.

        initialUnits = random.randint(1,10) # Set random  initial units between 1 and 10.
        
        auctionItems[itemName] = { # Dictionary for all items, their price and units associated.
            "price": initialPrice,
            "units": initialUnits
        }

        initialPrices[itemName] = {
            "price": initialPrice
        }

    pprint.pprint(auctionItems)

async def StartServer():
    global auctionItems 
    await InventoryGenerator()
    async with websockets.serve(HandleNewClient, '0.0.0.0', PORT) as server:
        print(f"[LISTENING] Server listening on port {PORT}")
        await ManageAuction()
        await server.serve_forever()

########################################### Server Startup Call

print("[STARTING]")
asyncio.run(StartServer())