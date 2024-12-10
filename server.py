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
listBids = []

###########################################

async def InventoryGenerator():
    print("[INVGEN] Generating Inventory:")
    items = {}

    for i in range(random.randint(10, 20)): # Sets range of number of items from 10 to 20.
        itemName = f"Item_{i + 1}" # What item number being displayed.
        
        initialPrice = random.randint(50, 500) # Set random initial price between 50 and 500.

        initialUnits = random.randint(1,10) # Set random  initial units between 1 and 10.
        
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
            {"name": itemName, "price": details["price"], "units": details["units"]}
            for itemName, details in auctionItems.items()
        ]
    }

    message = {"type":"auctionState", "items": auctionItems}

    if connectedClients:
        await asyncio.wait([client.send(message) for client in connectedClients])
    print("[BROADCAST] Current auction state sent to all clients")

async def HandleBid(websocket, item, bidAmount):                                        
    if not item in auctionItems:
        print("[ERROR] Item does not exist")
        nonexistent = json.dumps({"type":"bidResult", "response":"nonexistent"})
        await websocket.send(nonexistent)

    if auctionItems[item]["units"] <= 0:
        print("[ERROR] Item out of stock")
        unavailable = json.dumps({"type":"bidResult", "response":"unavailable"})
        await websocket.send(unavailable)

    if bidAmount <= auctionItems[item]["price"]:
        print("[REJECTED] Bid not beat current price")
        rejected = json.dumps({"type":"bidResult", "response":"rejected"})
        await websocket.send(rejected)

    ### If the code reaches this point, then the bid is valid ###

    print(f"[ACCEPTED] Bid on {item} accepted for {bidAmount}")

    auctionItems[item]["price"] = bidAmount                                         # Update to new highest bid
    listBids.append({"bidder": websocket, "item": item, "bidAmount": bidAmount})    # Add winning bid to list of bids
    listBids = sorted(listBids, key=lambda x: x["bidAmount"], reverse=True)         # Sort current bids by descending order of bid amount

    accepted = json.dumps({"type":"bidResult", "response":"accepted"})          # Notify bidder about win
    await websocket.send(accepted)

    await BroadcastItems(item, auctionItems[item])                              # Update all clients about current bid state

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
            
            print(f'[RECEIVED] {msg}')
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

async def StartServer():
    global auctionItems 
    auctionItems = await InventoryGenerator()
    await Timer() # Begin one minute timer
    async with websockets.serve(HandleNewClient, '0.0.0.0', PORT) as server:
        print(f"[LISTENING] Server listening on port {PORT}")
        await server.serve_forever()

async def Timer():
    print("[TIMER] Timer starts for 1 minute.")
    await asyncio.sleep(60)
    print("[TIMER] 1 minute is up.")

async def DecideWinner():
    print("[DECIDING WINNERS] Starting winner selection process")

   # Populate bids with actual data #FIXME
    bids = {item_name: [("client1", 100), ("client2", 150)] for item_name in auctionItems} 

    for item_name, bid_list in bids.items():
        if not bid_list:
            print(f"[NO BIDS] No bids received for {item_name}")
            continue

        sorted_bids = sorted(bid_list, key=lambda x: x[1], reverse=True)

        while auctionItems[item_name]["units"] > 0 and sorted_bids:
            winning_client, winning_bid = sorted_bids.pop(0)

            print(f"[WINNER] {winning_client} wins {item_name} with a bid of {winning_bid}")
            
            auctionItems[item_name]["units"] -= 1
            await NotifyClients(winning_client, item_name, winning_bid)
            auctionItems[item_name]["price"] = winning_bid

            winner_message = json.dumps({
                "type": "winner",
                "item": item_name,
                "bid_amount": winning_bid
            })
            await winning_client.send(winner_message)

        if auctionItems[item_name]["units"] <= 0:
            print(f"[OUT OF STOCK] {item_name} is now out of stock.")
        elif not sorted_bids:
            print(f"[NO MORE BIDS] No more bids for {item_name}")

    print("[DECIDING WINNERS] Winner selection process completed.")

async def NotifyClients(winning_client=None, winning_item=None, winning_bid=None):
    # Notify the winning client
    if winning_client and winning_item and winning_bid:
        winner_message = json.dumps({
            "type": "winNotification",
            "item": winning_item,
            "bidAmount": winning_bid,
            "message": f"Congratulations! You won {winning_item} with a bid of {winning_bid}."
        })
        await winning_client.send(winner_message)
        print(f"[NOTIFY WINNER] {winning_client.remote_address} won {winning_item} for {winning_bid}.")

        await BroadcastItems()
        
        print("[BROADCAST] Auction state updated and sent to all clients.")
        

async def ManageAuction():
    print("[AUCTION] Auction process has started.")
    
    while True:
        # Check if there are any items left to auction
        active_items = {item_name: details for item_name, details in auctionItems.items() if details["units"] > 0}
        
        if not active_items:
            print("[AUCTION END] All items have been sold. Auction is now closed.")
            await AnnounceFinalStatus()
            break

        print("[AUCTION ROUND] A new bidding round is starting.")
        print(f"[ACTIVE ITEMS] Items available for bidding: {list(active_items.keys())}")

        # Allow time for bids (e.g., 1 minute per round)
        await asyncio.sleep(60)  # Simulating a round duration

        # Simulate the selection of winners for items with bids
        await DecideWinner()

        # Broadcast updated auction state to all clients
        await NotifyClients()

        print("[AUCTION ROUND] Bidding round completed.")

async def AnnounceFinalStatus():
    print("[FINAL STATUS] Announcing final status of the auction.")
    final_status = {
        "type": "finalStatus",
        "items": auctionItems
    }

    pprint.pprint(auctionItems)

    if connectedClients:
        final_message = json.dumps(final_status)
        await asyncio.wait([client.send(final_message) for client in connectedClients])
        print("[FINAL STATUS] Sent to all clients.")

print("[STARTING]")
asyncio.run(StartServer())