/* This is your dashboard javascript, it has been embedded into dashboard.html */
//Load the Robot
function load_robot()
{
    document.getElementById("load").style.display = 'none';
    new_ajax_helper('/robotload', show_dashboard);
}

//Shutdown the Robot
function shutdown_robot()
{
    hide_dashboard();
    document.getElementById("load").style.display = 'none';
    new_ajax_helper('/robotshutdown', showloadbutton);
}

function showloadbutton()
{
    document.getElementById("load").style.display = 'block';
}

//Show the dashboard
function show_dashboard(results)
{
    document.getElementById("load").style.display = 'none';
    document.getElementById("dashboard").style.display = 'block';
    document.getElementById("videofeed").innerHTML = '<img src="/videofeed" width=100% />';
    console.log(results);
}

//Hide the dashboard
function hide_dashboard()
{
    document.getElementById("load").style.display = 'block';
    document.getElementById("dashboard").style.display = 'none';
    document.getElementById("videofeed").innerHTML = "";
}

//hide or show dashboard based on initial value from server on page load
if (robot_enabled == 1) {
    show_dashboard();
} else {
    hide_dashboard();
}

function printmessage(results)
{
    document.getElementById("message").innerText = results.message;
}

