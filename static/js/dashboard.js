/* This is your dashboard javascript, it has been embedded into dashboard.html */

//Load the Robot
function load_robot()
{
    alert("load");
    new_ajax_helper('/robotload', printmessage);
    show_dashbaord
}

//show the dashboard
function show_dashboard()
{
    document.getElementById("shutdown").style.display = 'block';
    document.getElementById("load").style.display = 'none';
    document.getElementById("dashboard").style.display = 'block';
}

//hide the dashboard
function hide_dashboard()
{
    document.getElementById("shutdown").style.display = 'none';
    document.getElementById("load").style.display = 'block';
    document.getElementById("dashboard").style.display = 'none';
}

//Shutdown the Robot
function shutdown_robot()
{
    new_ajax_helper('/robotshutdown', printmessage);

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