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
    hide_dashboard()
    new_ajax_helper('/robotshutdown', showloadbutton);
}

function showloadbutton()
{
    document.getElementById("load").style.display = 'block';
}

//show the dashboard
function show_dashboard(results)
{
    document.getElementById("load").style.display = 'none';
    document.getElementById("shutdown").style.display = 'block';
    document.getElementById("dashboard").style.display = 'block';
    document.getElementById("message").innerText = JSON.stringify(results);
}

//hide the dashboard
function hide_dashboard()
{
    document.getElementById("shutdown").style.display = 'none';
    document.getElementById("load").style.display = 'block';
    document.getElementById("dashboard").style.display = 'none';
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