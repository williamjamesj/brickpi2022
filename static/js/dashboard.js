/* This is your dashboard javascript, it has been embedded into dashboard.html */

//Load the BrickPi
function loadrobot()
{
    alert("load");
    new_ajax_helper('/brickpiload', printmessage);
    document.getElementById("shutdown").style.display = 'block';
    document.getElementById("load").style.display = 'none';
}

//Shutdown the BrickPi
function shutdownrobot()
{
    alert("shutdown");
    new_ajax_helper('/brickpishutdown', printmessage);
    document.getElementById("shutdown").style.display = 'none';
    document.getElementById("load").style.display = 'block';
}

function printmessage(results)
{
    document.getElementById("message").innerText = results.message;
}