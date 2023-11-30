//global socket
let socket = null

function websocketConn(id){
    console.log("loaded", id)
    socket = io('//url', {
        transports: ['websocket']
    });

    console.log("interval")
    getAuctionTime(id)
    setInterval(() => {getAuctionTime(id)}, 1000);
}

function submitForm(){
    let form = new FormData(document.querySelector("form"))
    console.log("sending")
    for (const iterator of form) {

        console.log(iterator)
    }
    socket.emit("new post", {form: form})
}

function getAuctionTime(id){
    socket.emit("time", {id:id}, (data) => {
        let time
        if (data > 0){
            // console.log(new Date(data * 1000).toISOString().slice(11, 19))

            // brute force solution if for some reason the date stuff stops working
            // var hours   = Math.floor(data / 3600)
            // var minutes = Math.floor(data / 60) % 60
            // var seconds = data % 60
            // time = `${hours}:${minutes}:${seconds}`

            time = new Date(data * 1000).toISOString().slice(11, 19)
        }
        else{
            time = "Auction Ended :("
        }        
        document.getElementById("time").innerText = time
    })

}

function submitBid(id){
    
    let bid = document.getElementById("user-bid").value
    // socket.emit("submit_bid", { bid: user-bid, post_id: id })
    console.log(id, bid)

    socket.emit("submitBid",  { bid: bid, _id: id }, (data) => {
        //do something
        console.log(data)

        let result = data.updated

        let highest = document.getElementById("highest")
        let winner = document.getElementById("winner")
        let feedback = document.getElementById("bid-result")
        if (result == false){
            feedback.innerText = "Bid not accepted :( Try Higher!"
            highest.innerText = data.bid
            winner.innerText = data.winner

        } else if (result == true){
            feedback.innerText = "Woah, bid accepted! You're one step closer to getting this!"
            highest.innerText = data.bid
            winner.innerText = data.winner

        } else if (result == "redirect"){
            window.location.href = "/"
            console.log("redirect")
        }
    })
}

