/////////////////////////////////////////////////////////////////////// Constants + Globals

const ADDR = 'localhost'; // Local IPv4 goes here
let socket;
let auctionState = []; // holds the auction state

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
        console.log('[WEBSOCKET] Sent: ', msg);
    } 
    else {
        console.error('[WEBSOCKET ERROR] WebSocket is not open.');
    }
}

function HandleServerMessage(message) {
    let rcvdJson = JSON.parse(message);

    if (rcvdJson["type"] == "auctionState") {
        auctionState = rcvdJson["items"];
        console.log('[AUCTION STATE]:\n' + JSON.stringify(auctionState,null,2));
        UpdateTable();
    }
    else if (rcvdJson["type"] == "bidResult") {
        let str = "[BID RESULT] ";
        str += rcvdJson["response"];
        console.log(str);
    }
    else if (rcvdJson["type"] == "auctionResult") {

    }
}

function UpdateTable() {
    let str = '<table>'
    + '<tr>'
    + '<th>Item Name</th>'
    + '<th>Current Bid Price</th>'
    + '<th>Units Left</th>'
    + '</tr>'

    for (let key in auctionState) {
        const {price,units} = auctionState[key];

        str += '<tr>'
        + '<td>' + key.replace('_',' ') + '</td>'
        + '<td>$' + price + '</td>'
        + '<td>' + units + '</td>'
        + '</tr>'
     }

    str += '</table>'
    str += '<button type="button" class="main_button" onclick="AutoBid()">Begin Bidding</button>'

    document.getElementById("display").innerHTML = str;
}

/////////////////////////////////////////////////////////////////////// Bidding Functions

function AutoBid() {
    auctionState.forEach( (selectedItem) =>{
        if (selectedItem.units <=0){
            console.log(`[AUTO BID] ${selectedItem.name} is out of stock.`)
            return;
        }
        if (Math.random() < 0.3) {
            console.log(`[AUTO BID] Skipping ${selectedItem.name} this round`);
            return;
        }

        const itemName = selectedItem.name;
        const currentPrice = selectedItem.price;

        if (!clientMaxBids[itemName]){
            const randomIncrement = Math.floor(Math.random() * (500 - currentPrice + 1)); // Random between currentPrice and 500
            clientMaxBids[itemName] = currentPrice + randomIncrement;
        }
        const maxPrice = clientMaxBids[itemName];

        if (currentPrice < maxPrice){
            const bidAmount = currentPrice + Math.floor(Math.random() * 10) + 1; //1-10
            const bid = JSON.stringify({
                item: itemName,
                bid_amount: bidAmount
            });
            console.log(`[AUTO BID] Bidding ${bidAmount} on ${itemName} (current price: ${currentPrice}, max price: ${maxPrice})`);
            SendMessage(bid);
        }   
        else{
            console.log(`[AUTO BID] Not bidding on ${itemName}. Current price: ${currentPrice}, max price: ${maxPrice}`);
        }
    });

}

function Init() {
    EstablishConnection().then(() => {
        // any other code to run after the connection successfully establishes
        
    })
    .catch((error) => {
        console.error('[WEBSOCKET ERROR] Failed to establish connection:', error);
    });
}