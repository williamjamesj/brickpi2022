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
    document.getElementById("shutdown").style.display = 'none';
    new_ajax_helper('/robotshutdown', hide_dashboard);
}

//show the dashboard
function show_dashboard(results)
{
    alert("Waiting");
    document.getElementById("load").style.display = 'none';
    document.getElementById("shutdown").style.display = 'block';
    document.getElementById("dashboard").style.display = 'block';
    document.getElementById("message").innerText = JSON.stringify(results.message);
}

//hide the dashboard
function hide_dashboard(results)
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