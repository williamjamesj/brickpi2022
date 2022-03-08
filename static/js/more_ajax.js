// This code sends a JSON dictionary to the server, and is capable of recieving data back from the server if necesasry.
function send_data(url, data, responseDestination=receivedResponse) {
    $.ajax({
        type: "POST", 
        url: url,
        data: JSON.stringify(data),
        contentType: "application/json",
        dataType: "json",
        success: function(result) {
            responseDestination(result);
        }
    });
}
function receivedResponse(result) {
    console.log(result);
}