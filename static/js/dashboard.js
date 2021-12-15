/* This is your dashboard javascript, it has been embedded into dashboard.html */

//Load the Robot
function loadrobot()
{
    alert("load");
    new_ajax_helper('/robotload', printmessage);
    document.getElementById("shutdown").style.display = 'block';
    document.getElementById("load").style.display = 'none';
}

//Shutdown the Robot
function shutdownrobot()
{
    alert("shutdown");
    new_ajax_helper('/robotshutdown', printmessage);
    document.getElementById("shutdown").style.display = 'none';
    document.getElementById("load").style.display = 'block';
}

function printmessage(results)
{
    document.getElementById("message").innerText = results.message;
}