/////////////////////////////////////////////////////////////////////// Constants + Globals

const ADDR = 'localhost';   // address of the server (IPv4 goes here)
const discon = "!DISCONNECT";
let socket;
let auctionState = [];      // holds the auction state
let maxBids = [];           // a list of items the bidder wants and the max they'll be willing to pay for them
let currBids = [];          // a list of items the bidder has bid on and the last amount they bid (to prevent feedback loops where the bidder tries to beat itself)
let itemsWon = [];          // a list of items the bidder has won and the amount of each
let isBidding = false;

/////////////////////////////////////////////////////////////////////// Client<->Server Functions

function EstablishConnection() {
    return new Promise((resolve, reject) => {
        socket = new WebSocket('ws://' + ADDR + ':5050');

        socket.onopen = function() {
            console.log('[WEBSOCKET] Connection established.');
            resolve(); // Resolve the promise
        };

        socket.onerror = function(error) {
            console.error('[WEBSOCKET ERROR] ', error);
            reject(error); // Reject the promise on error
        };

        socket.onclose = function() {
            console.log('[WEBSOCKET] WebSocket connection closed.');
        };

        socket.onmessage = function(event) {
            //console.log('[WEBSOCKET] Message received from server:\n', event.data);
            HandleServerMessage(event.data);
        };
    });
}

function SendMessage(msg) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(msg);
        //console.log('[WEBSOCKET] Sent: ', msg);
    } 
    else {
        console.error('[WEBSOCKET ERROR] WebSocket is not open.');
    }
}

function HandleServerMessage(message) {
    let rcvdJson = JSON.parse(message);

    if (rcvdJson["type"] == "auctionState") {
        auctionState = rcvdJson["items"];
        //console.log('[NEW AUCTION STATE]:\n' + JSON.stringify(auctionState,null,2));
        UpdateTable();       // Update the table to reflect new auction status
        setTimeout(SendBids, 1000);         // Bid again
    }
    else if (rcvdJson["type"] == "bidResult") {
        let str = "[BID RESULT] ";
        str += rcvdJson["response"];        
        console.log(str);
    }
    else if (rcvdJson["type"] == "rewardedItem") {
        let item = rcvdJson["item"];
        console.log("[ITEM WON]: " + item);
        itemsWon[item] = itemsWon[item] ? itemsWon[item] + 1 : 1;
        isBidding = false;
        UpdateClientBidsTable();
    }
    else if (rcvdJson["type"] == "updateQuantities") {
        auctionState = rcvdJson["items"];
        UpdateTable();
    }
    else if (rcvdJson["type"] == "newRound") {
        console.log("[NEW ROUND]")
        auctionState = rcvdJson["items"];
        UpdateTable();
        InitBids();
    }
    else if (rcvdJson["type"] == "auctionOver") {
        alert("Auction over!")
    }
}

function LeaveAuction() {
    if (isBidding) {
        alert("Can't leave in the middle of a round!");
        return;
    }

    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(discon);
    } 
    else {
        console.error('[WEBSOCKET ERROR] WebSocket is not open.');
    }
}

/////////////////////////////////////////////////////////////////////// Misc. Client-side Functions

function Init() {
    EstablishConnection().then(() => {
        // any other code to run after the connection successfully establishes
        
    })
    .catch((error) => {
        console.error('[WEBSOCKET ERROR] Failed to establish connection:', error);
    });
}

function UpdateTable() {
    let str = '<tr>'
    + '<th>Item</th>'
    + '<th>Current Bid Price</th>'
    + '<th>Units Left</th>'
    + '</tr>'

    for (let item in auctionState) {
        const {price,units} = auctionState[item];

        str += '<tr>'
        + '<td>' + item.replace('_',' ') + '</td>'
        + '<td>$' + price + '</td>'
        + '<td>' + units + '</td>'
        + '</tr>'
     }

    document.getElementById("auction_state").innerHTML = str;
}

/////////////////////////////////////////////////////////////////////// Bidding

function UpdateClientBidsTable() {
    //console.log("[YOUR BIDS] Updating your bids and items owned...");
    let str = '<tr>'
    + '<th>Wanted</th>'
    + '<th>Item Name</th>'
    + '<th>Current</th>'
    + '<th>Limit</th>'
    + '<th># Won</th>'
    + '</tr>'

    for (let item in auctionState) {

        str += '<tr>'
        + '<td>' + (maxBids[item] ? 'Yes' : 'No') + '</td>'
        + '<td>' + item.replace('_',' ') + '</td>'
        + '<td>' + (currBids[item] ? ('$' + currBids[item]) : 'N/A') + '</td>'
        + '<td>' + (maxBids[item] ? ('$' + maxBids[item]) : 'N/A') + '</td>'
        + '<td>' + (itemsWon[item] == undefined ? 0 : itemsWon[item]) + '</td>'
        + '</tr>'
     }

    document.getElementById("client_bids").innerHTML = str;
}

function InitBids() { // Establish desired items and maximum price we are willing to pay for those items (called per round)
    maxBids = [];   // Reset max bids
    currBids = [];  // Reset current bids
    isBidding = true;

    console.log("[INIT BID] Updating bids...\n=============================");
    for (let item in auctionState) {
        
        const currentPrice = auctionState[item]["price"];
        const unitsAvailable = auctionState[item]["units"];

        if (unitsAvailable <= 0) {
            console.log(`[INIT BID] ${item} is out of stock.`);
            continue;
        }

        if (!maxBids[item]){
            if (Math.random() < 0.3) {
                console.log(`[INIT BID] Skipping ${item.replace('_',' ')} this round.`);
                continue;
            }
            
            console.log('[INIT BID] Selected ' + item.replace('_',' ') + ' to bid on.');

            const randomIncrement = Math.floor(Math.random() * (500 - currentPrice + 1)); // Random between currentPrice and 500
            console.log("[INIT BID] No max price defined for " + item.replace('_',' ') + ', setting to $' + (currentPrice + randomIncrement))
            maxBids[item] = currentPrice + randomIncrement;
        }

        console.log("=============================");
    }

    UpdateClientBidsTable();
    SendBids(); // Send initial bids

    document.getElementById("bid_button").innerHTML = '<button type="button" onclick=LeaveAuction()>Leave Auction</button>'
}

function SendBids() {
    if (!isBidding) {
        return;
    }
    console.log("[BIDDING ATTEMPT]")
    for (let item in maxBids) {        
        const currentPrice = auctionState[item]["price"];
        const unitsAvailable = auctionState[item]["units"];
        const maxPrice = maxBids[item]

        if (unitsAvailable <= 0) {
            console.log(`[BID] ${item} is out of stock, skipping.`);
            continue;
        }

        if (currentPrice == currBids[item]) {
            console.log("[BID] Last leading bid was ours, skip this item")
            continue;
        }

        console.log("[BID] Attemping to beat current bid for " + item.replace('_',' '))
        if (currentPrice < maxPrice){
            const bidAmount = currentPrice + Math.floor(Math.random() * 10) + 1; //1-10

            const bid = JSON.stringify({
                item: item,
                bid_amount: bidAmount
            });


            console.log(`[BID] Bidding $${bidAmount} on ${item.replace('_',' ')} (current price: ${currentPrice}, max price: ${maxPrice})`);
            SendMessage(bid);
            currBids[item] = bidAmount;
        }
        else {
            console.log(`[BID] Not bidding on ${item.replace('_',' ')}. Current price: ${currentPrice}, max price: ${maxPrice}`);
        }
    }

    UpdateClientBidsTable();
}